"""Payments router — creates Nexi HPP sessions, receives webhooks, and drives
the order state machine + license delivery via Brevo.

State machine:
  draft → pending_payment → paid → fulfillment_pending → fulfilled
  pending_payment → failed | cancelled
  paid → refunded (post-hoc)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, Body

import nexi_xpay
from services import license_inventory
from services.email_brevo import (
    send_email, order_confirmation_html, license_delivery_html, BrevoError,
    pdf_attachment,
)
from config import COMMERCE_ENABLED

log = logging.getLogger("licenzpol.payments")
payments_router = APIRouter(prefix="/api/payments")


def _db(req: Request):
    return req.app.state.db


# ---------- Create HPP -----------------------------------------------------

@payments_router.post("/create/{order_reference}")
async def create_payment_for_order(order_reference: str, request: Request):
    """Given a previously-created order, initialize a Nexi HPP session and
    return the hostedPage URL for the client to redirect to."""
    if not COMMERCE_ENABLED:
        raise HTTPException(status_code=503, detail="Commerce non ancora attivo.")
    if not nexi_xpay.is_configured():
        raise HTTPException(status_code=503, detail="Nexi XPay non configurato.")

    db = _db(request)
    order = await db.orders.find_one({"reference": order_reference})
    if not order:
        raise HTTPException(status_code=404, detail="Ordine non trovato.")
    if order.get("status") not in {"pending_payment", "draft", "demo_confirmed"}:
        return {
            "already_processed": True,
            "status": order.get("status"),
            "reference": order_reference,
        }

    items = order.get("items") or []
    if not items:
        raise HTTPException(status_code=400, detail="Ordine vuoto.")

    # Pre-reserve one license key per line item BEFORE contacting Nexi.
    # If we cannot reserve, refuse the payment (no fulfillment possible).
    reserved = []
    try:
        for line in items:
            qty = int(line.get("quantity") or 1)
            sku = line.get("sku")
            if not sku:
                raise HTTPException(status_code=400, detail=f"Il prodotto {line.get('product_name')} non ha SKU merchant.")
            for _ in range(qty):
                doc = await license_inventory.reserve_key(db, sku, order_reference)
                if not doc:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Nessuna licenza disponibile per {line.get('product_name')}. Riprova più tardi.",
                    )
                reserved.append({"sku": sku, "license_id": str(doc.get("_id") or doc.get("id"))})
    except HTTPException:
        # Release anything we already booked before raising.
        await license_inventory.release_reservation(db, order_reference)
        raise
    except Exception:
        await license_inventory.release_reservation(db, order_reference)
        raise

    try:
        desc = f"LicenzPol {order_reference} · {len(items)} art."
        session = await nexi_xpay.create_hosted_payment(
            order_reference=order_reference,
            total_eur=float(order["total_eur"]),
            description=desc,
        )
    except nexi_xpay.NexiError as e:
        # Release reservations if Nexi fails to accept the payment
        await license_inventory.release_reservation(db, order_reference)
        log.error("Nexi HPP failed for %s: %s", order_reference, e)
        raise HTTPException(status_code=502, detail=f"Errore Nexi: {e}")

    await db.orders.update_one(
        {"reference": order_reference},
        {"$set": {
            "status": "pending_payment",
            "psp": "nexi",
            "psp_order_id": session["orderId"],
            "psp_security_token": session["securityToken"],
            "psp_hosted_page": session["hostedPage"],
            "psp_created_at": datetime.now(timezone.utc).isoformat(),
            "reserved_licenses": reserved,
        }},
    )
    return {
        "hosted_page": session["hostedPage"],
        "reference": order_reference,
        "psp": "nexi",
    }


# ---------- Webhook --------------------------------------------------------

@payments_router.post("/nexi/webhook", status_code=200)
async def nexi_webhook(request: Request, body: dict = Body(...)):
    db = _db(request)
    operation = (body.get("operation") or {})
    order_id = operation.get("orderId")
    event_id = body.get("eventId")
    supplied_token = body.get("securityToken")

    log.info("nexi webhook event=%s order=%s op=%s", event_id, order_id,
             operation.get("operationResult"))

    if not order_id or not event_id or not supplied_token:
        raise HTTPException(status_code=400, detail="Malformed notification.")

    saved = await db.orders.find_one({"psp_order_id": order_id})
    if not saved:
        # Fallback: some Nexi accounts prefix orderIds
        saved = await db.orders.find_one({"reference": order_id})
    if not saved:
        raise HTTPException(status_code=400, detail="Unknown order.")

    if not nexi_xpay.verify_notification_token(supplied_token, saved.get("psp_security_token", "")):
        log.warning("nexi webhook token mismatch for order=%s", order_id)
        raise HTTPException(status_code=401, detail="Invalid notification token.")

    # Idempotency: if we've already processed this event, ignore.
    existing = await db.psp_events.find_one({"event_id": event_id})
    if existing:
        return {"ok": True, "duplicate": True}

    await db.psp_events.insert_one({
        "event_id": event_id,
        "order_reference": saved["reference"],
        "operation": operation,
        "received_at": datetime.now(timezone.utc).isoformat(),
    })

    new_status = nexi_xpay.map_result_to_status(operation.get("operationResult"))

    await db.orders.update_one(
        {"reference": saved["reference"]},
        {"$set": {
            "status": new_status,
            "psp_operation_id": operation.get("operationId"),
            "psp_last_event_at": datetime.now(timezone.utc).isoformat(),
        }},
    )

    if new_status == "paid":
        await _fulfil_order(request, saved["reference"])
    elif new_status in {"failed", "cancelled"}:
        await license_inventory.release_reservation(db, saved["reference"])

    return {"ok": True}


# ---------- Status query ---------------------------------------------------

@payments_router.get("/status/{order_reference}")
async def payment_status(order_reference: str, request: Request):
    db = _db(request)
    order = await db.orders.find_one({"reference": order_reference})
    if not order:
        raise HTTPException(status_code=404, detail="Ordine non trovato.")
    # If we've got a PSP order id, re-query authoritatively.
    psp_status = None
    if order.get("psp_order_id"):
        try:
            psp_status = await nexi_xpay.query_order(order["psp_order_id"])
            ops = (psp_status.get("operations") or [])
            if ops:
                mapped = nexi_xpay.map_result_to_status(ops[-1].get("operationResult"))
                if mapped != order.get("status"):
                    await db.orders.update_one(
                        {"reference": order_reference},
                        {"$set": {"status": mapped,
                                  "psp_last_query_at": datetime.now(timezone.utc).isoformat()}},
                    )
                    order["status"] = mapped
                    if mapped == "paid":
                        await _fulfil_order(request, order_reference)
        except nexi_xpay.NexiError as e:
            log.warning("Failed to query Nexi for %s: %s", order_reference, e)

    return {
        "reference": order_reference,
        "status": order["status"],
        "total_eur": order.get("total_eur"),
        "psp_status_raw": psp_status,
    }


# ---------- Fulfilment -----------------------------------------------------

async def _fulfil_order(request: Request, order_reference: str) -> None:
    """Deliver the license keys via Brevo and mark the order fulfilled.

    Idempotent: if already fulfilled we do nothing.
    """
    db = _db(request)
    order = await db.orders.find_one({"reference": order_reference})
    if not order:
        return
    if order.get("status") == "fulfilled":
        return

    keys = await license_inventory.get_keys_for_order(db, order_reference)
    reserved_keys = [k for k in keys if k.get("status") == "reserved"]

    if not reserved_keys:
        log.warning("Fulfilment: no reserved keys for order %s", order_reference)
        return

    # Send license delivery email(s)
    try:
        for line in order.get("items", []):
            sku = line.get("sku")
            product_name = line.get("product_name")
            # Group by SKU
            sku_keys = [k for k in reserved_keys if k.get("sku") == sku]
            for k in sku_keys[: int(line.get("quantity") or 1)]:
                try:
                    plaintext = license_inventory.decrypt_key(k["key_encrypted"])
                except Exception:
                    plaintext = "[chiave criptata — contatta supporto]"
                html = license_delivery_html(
                    customer_name=order.get("first_name") or order.get("email"),
                    order_ref=order_reference,
                    product_name=product_name,
                    license_key=plaintext,
                )
                await send_email(
                    to_email=order["email"],
                    to_name=f"{order.get('first_name','')} {order.get('last_name','')}".strip(),
                    subject=f"La tua licenza {product_name} · Ordine {order_reference}",
                    html=html,
                    tags=["license-delivery", f"order-{order_reference}"],
                )
        await license_inventory.mark_delivered(db, order_reference)
        await db.orders.update_one(
            {"reference": order_reference},
            {"$set": {
                "status": "fulfilled",
                "fulfilled_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        log.info("Order %s fulfilled and delivered.", order_reference)
    except BrevoError as e:
        log.error("Brevo failed for %s: %s", order_reference, e)
        await db.orders.update_one(
            {"reference": order_reference},
            {"$set": {
                "status": "fulfillment_pending",
                "fulfillment_error": str(e),
            }},
        )


# ---------- Public config for the frontend ---------------------------------

@payments_router.get("/config")
async def payments_config():
    return {
        "commerce_enabled": COMMERCE_ENABLED,
        "psp": "nexi" if nexi_xpay.is_configured() else None,
        "env": (
            "production" if nexi_xpay.base_url() == nexi_xpay.PROD_BASE
            else "sandbox"
        ),
    }
