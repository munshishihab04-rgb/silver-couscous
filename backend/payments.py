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
from fastapi import APIRouter, HTTPException, Request, Body, Header
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

import nexi_xpay
from services import license_inventory, email_outbox, transactional_dispatch
from services.email_brevo import (
    send_email, order_confirmation_html, license_delivery_html, BrevoError,
    pdf_attachment,
)
from config import COMMERCE_ENABLED
from order_access import verify_order_token

log = logging.getLogger("licenzpol.payments")
payments_router = APIRouter(prefix="/api/payments")


def _db(req: Request):
    return req.app.state.db


def should_initialize_payment(order: dict) -> bool:
    return order.get("status") in {"draft", "demo_confirmed"} and not order.get("psp_order_id")


def should_finalize_delivery(message_ids: list[str]) -> bool:
    return bool(message_ids) and all(not message_id.startswith("dry-run:") for message_id in message_ids)


_ALLOWED_TRANSITIONS = {
    "draft": {"draft", "payment_initializing", "pending_payment", "cancelled"},
    "demo_confirmed": {"demo_confirmed", "payment_initializing", "pending_payment", "cancelled"},
    "payment_initializing": {"payment_initializing", "draft", "demo_confirmed", "pending_payment", "cancelled"},
    "pending_payment": {"pending_payment", "paid", "failed", "cancelled"},
    "paid": {"paid", "fulfillment_processing", "fulfillment_pending", "fulfilled", "refunded"},
    "fulfillment_processing": {"fulfillment_processing", "fulfillment_pending", "fulfilled"},
    "fulfillment_pending": {"fulfillment_pending", "fulfillment_processing", "fulfilled", "refunded"},
    "fulfilled": {"fulfilled", "refunded"},
    "failed": {"failed"},
    "cancelled": {"cancelled"},
    "refunded": {"refunded"},
}


def can_transition(current: str | None, target: str | None) -> bool:
    return bool(current and target and target in _ALLOWED_TRANSITIONS.get(current, set()))


def sanitize_psp_operation(operation: dict) -> dict:
    allowed = ("orderId", "operationId", "operationResult", "operationType")
    return {
        key: str(operation[key])[:160]
        for key in allowed
        if operation.get(key) is not None
    }


async def claim_fulfillment(db, order_reference: str):
    return await db.orders.find_one_and_update(
        {"reference": order_reference, "status": {"$in": ["paid", "fulfillment_pending"]}},
        {
            "$set": {
                "status": "fulfillment_processing",
                "fulfillment_claimed_at": datetime.now(timezone.utc).isoformat(),
            },
            "$inc": {"fulfillment_attempts": 1},
        },
        return_document=ReturnDocument.AFTER,
    )


async def claim_payment_initialization(db, order_reference: str, current_status: str) -> bool:
    result = await db.orders.update_one(
        {"reference": order_reference, "status": current_status, "psp_order_id": {"$exists": False}},
        {"$set": {
            "status": "payment_initializing",
            "payment_initialization_started_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return result.modified_count == 1


async def reset_payment_initialization(db, order_reference: str, original_status: str) -> None:
    await db.orders.update_one(
        {"reference": order_reference, "status": "payment_initializing"},
        {
            "$set": {"status": original_status},
            "$unset": {"payment_initialization_started_at": ""},
        },
    )


async def _queue_order_email(db, order: dict, *, template: str, suffix: str, support_code: str | None = None) -> None:
    event_key = f"order:{order['reference']}:{suffix}"
    context = {
        "customer_name": order.get("first_name") or order.get("email"),
        "order_reference": order["reference"],
        "total_eur": float(order.get("total_eur") or 0),
    }
    if support_code:
        context["support_code"] = support_code
    await email_outbox.enqueue(
        db,
        event_key=event_key,
        template=template,
        recipient=order["email"],
        context=context,
    )
    try:
        await transactional_dispatch.dispatch(db, event_key)
    except Exception:
        log.exception("Transactional status email failed for order %s", order["reference"])


# ---------- Create HPP -----------------------------------------------------

@payments_router.post("/create/{order_reference}")
async def create_payment_for_order(
    order_reference: str,
    request: Request,
    x_order_token: Optional[str] = Header(default=None, alias="X-Order-Token"),
):
    """Given a previously-created order, initialize a Nexi HPP session and
    return the hostedPage URL for the client to redirect to."""
    if not COMMERCE_ENABLED:
        raise HTTPException(status_code=503, detail="Commerce non ancora attivo.")
    if not nexi_xpay.is_configured():
        raise HTTPException(status_code=503, detail="Nexi XPay non configurato.")

    db = _db(request)
    order = await db.orders.find_one({"reference": order_reference})
    if not order or not verify_order_token(x_order_token, order.get("access_token_hash")):
        raise HTTPException(status_code=404, detail="Ordine non trovato.")
    if not should_initialize_payment(order):
        return {
            "already_processed": True,
            "status": order.get("status"),
            "reference": order_reference,
        }

    items = order.get("items") or []
    if not items:
        raise HTTPException(status_code=400, detail="Ordine vuoto.")

    original_status = order["status"]
    if not await claim_payment_initialization(db, order_reference, original_status):
        current = await db.orders.find_one({"reference": order_reference}, {"status": 1})
        return {
            "already_processed": True,
            "status": current.get("status") if current else "unknown",
            "reference": order_reference,
        }

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
        await reset_payment_initialization(db, order_reference, original_status)
        raise
    except Exception:
        await license_inventory.release_reservation(db, order_reference)
        await reset_payment_initialization(db, order_reference, original_status)
        raise

    try:
        desc = f"LicenzPol {order_reference} · {len(items)} art."
        session = await nexi_xpay.create_hosted_payment(
            order_reference=order_reference,
            total_eur=float(order["total_eur"]),
            description=desc,
        )
    except Exception as e:
        # Any provider/network failure must release inventory and reset the claim.
        await license_inventory.release_reservation(db, order_reference)
        await reset_payment_initialization(db, order_reference, original_status)
        log.error("Nexi HPP failed for %s (%s)", order_reference, type(e).__name__)
        raise HTTPException(status_code=502, detail="Errore temporaneo del provider di pagamento.")

    transition = await db.orders.update_one(
        {"reference": order_reference, "status": "payment_initializing"},
        {"$set": {
            "status": "pending_payment",
            "psp": "nexi",
            "psp_order_id": session["orderId"],
            "psp_security_token": session["securityToken"],
            "psp_hosted_page": session["hostedPage"],
            "psp_created_at": datetime.now(timezone.utc).isoformat(),
            "reserved_licenses": reserved,
        }, "$unset": {"payment_initialization_started_at": ""}},
    )
    if transition.modified_count != 1:
        await license_inventory.release_reservation(db, order_reference)
        await reset_payment_initialization(db, order_reference, original_status)
        raise HTTPException(status_code=409, detail="Inizializzazione pagamento concorrente; operazione bloccata.")
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
    if len(str(order_id)) > 160 or len(str(event_id)) > 160 or len(str(supplied_token)) > 512:
        raise HTTPException(status_code=400, detail="Malformed notification.")
    order_id, event_id, supplied_token = str(order_id), str(event_id), str(supplied_token)

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

    try:
        await db.psp_events.insert_one({
            "event_id": event_id,
            "order_reference": saved["reference"],
            "operation": sanitize_psp_operation(operation),
            "received_at": datetime.now(timezone.utc).isoformat(),
        })
    except DuplicateKeyError:
        return {"ok": True, "duplicate": True}

    new_status = nexi_xpay.map_result_to_status(operation.get("operationResult"))
    current_status = saved.get("status")
    if not can_transition(current_status, new_status):
        log.warning("Rejected order transition %s -> %s for %s", current_status, new_status, saved["reference"])
        return {"ok": True, "ignored": "invalid_transition"}

    transition = await db.orders.update_one(
        {"reference": saved["reference"], "status": current_status},
        {"$set": {
            "status": new_status,
            "psp_operation_id": operation.get("operationId"),
            "psp_last_event_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    if transition.modified_count == 0 and new_status != current_status:
        return {"ok": True, "duplicate": True, "reason": "concurrent_transition"}

    if new_status == "paid":
        await _queue_order_email(db, saved, template="payment_confirmed", suffix="payment-confirmed")
        await _fulfil_order(request, saved["reference"])
    elif new_status in {"failed", "cancelled"}:
        await license_inventory.release_reservation(db, saved["reference"])
        await _queue_order_email(
            db,
            saved,
            template="order_problem",
            suffix=new_status,
            support_code=f"{new_status.upper()}-{saved['reference']}",
        )

    return {"ok": True}


# ---------- Status query ---------------------------------------------------

@payments_router.get("/status/{order_reference}")
async def payment_status(
    order_reference: str,
    request: Request,
    x_order_token: Optional[str] = Header(default=None, alias="X-Order-Token"),
):
    db = _db(request)
    order = await db.orders.find_one({"reference": order_reference})
    if not order or not verify_order_token(x_order_token, order.get("access_token_hash")):
        raise HTTPException(status_code=404, detail="Ordine non trovato.")
    # If we've got a PSP order id, re-query authoritatively.
    psp_status = None
    if order.get("psp_order_id"):
        try:
            psp_status = await nexi_xpay.query_order(order["psp_order_id"])
            ops = (psp_status.get("operations") or [])
            if ops:
                mapped = nexi_xpay.map_result_to_status(ops[-1].get("operationResult"))
                if mapped != order.get("status") and can_transition(order.get("status"), mapped):
                    transition = await db.orders.update_one(
                        {"reference": order_reference, "status": order.get("status")},
                        {"$set": {"status": mapped,
                                  "psp_last_query_at": datetime.now(timezone.utc).isoformat()}},
                    )
                    if transition.modified_count:
                        order["status"] = mapped
                        if mapped == "paid":
                            await _queue_order_email(db, order, template="payment_confirmed", suffix="payment-confirmed")
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
    order = await claim_fulfillment(db, order_reference)
    if not order:
        return

    keys = await license_inventory.get_keys_for_order(db, order_reference)
    reserved_keys = [k for k in keys if k.get("status") == "reserved"]

    if not reserved_keys:
        log.warning("Fulfilment: no reserved keys for order %s", order_reference)
        await db.orders.update_one(
            {"reference": order_reference, "status": "fulfillment_processing"},
            {"$set": {"status": "fulfillment_pending", "fulfillment_error_code": "reserved_keys_missing"}},
        )
        return

    delivery_event_key = f"order:{order_reference}:license-delivery"
    await email_outbox.enqueue(
        db,
        event_key=delivery_event_key,
        template="license_delivery",
        recipient=order["email"],
        context={"order_reference": order_reference},
    )
    delivery_event = await email_outbox.claim(db, delivery_event_key)
    if not delivery_event:
        await db.orders.update_one(
            {"reference": order_reference, "status": "fulfillment_processing"},
            {"$set": {"status": "fulfillment_pending", "fulfillment_error_code": "delivery_event_already_processed"}},
        )
        return

    # Send license delivery email(s). Plaintext keys exist only in memory.
    message_ids: list[str] = []
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
                    log.error("License decryption failed for order %s", order_reference)
                    await email_outbox.mark_failed(db, delivery_event_key, "license_decryption_failed")
                    await db.orders.update_one(
                        {"reference": order_reference, "status": "fulfillment_processing"},
                        {"$set": {"status": "fulfillment_pending", "fulfillment_error_code": "license_decryption_failed"}},
                    )
                    return
                html = license_delivery_html(
                    customer_name=order.get("first_name") or order.get("email"),
                    order_ref=order_reference,
                    product_name=product_name,
                    license_key=plaintext,
                )
                message_id = await send_email(
                    to_email=order["email"],
                    to_name=f"{order.get('first_name','')} {order.get('last_name','')}".strip(),
                    subject=f"La tua licenza {product_name} · Ordine {order_reference}",
                    html=html,
                    tags=["license-delivery", f"order-{order_reference}"],
                )
                message_ids.append(message_id)
        if not should_finalize_delivery(message_ids):
            await email_outbox.mark_sent(
                db,
                delivery_event_key,
                ",".join(message_ids)[:500],
                dry_run=True,
            )
            await db.orders.update_one(
                {"reference": order_reference, "status": "fulfillment_processing"},
                {"$set": {
                    "status": "fulfillment_pending",
                    "fulfillment_error_code": "email_dry_run",
                    "email_dry_run_ids": message_ids,
                }},
            )
            return
        await email_outbox.mark_sent(
            db,
            delivery_event_key,
            ",".join(message_ids)[:500],
            dry_run=False,
        )
        await license_inventory.mark_delivered(db, order_reference)
        await db.orders.update_one(
            {"reference": order_reference, "status": "fulfillment_processing"},
            {"$set": {
                "status": "fulfilled",
                "fulfilled_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        log.info("Order %s fulfilled and delivered.", order_reference)
    except BrevoError as e:
        log.error("Brevo delivery failed for order %s (%s)", order_reference, type(e).__name__)
        await email_outbox.mark_failed(db, delivery_event_key, "email_provider_failed")
        await db.orders.update_one(
            {"reference": order_reference, "status": "fulfillment_processing"},
            {"$set": {
                "status": "fulfillment_pending",
                "fulfillment_error_code": "email_provider_failed",
            }},
        )
    except Exception as e:
        log.error("Fulfillment failed for order %s (%s)", order_reference, type(e).__name__)
        await email_outbox.mark_failed(db, delivery_event_key, "internal_fulfillment_error")
        await db.orders.update_one(
            {"reference": order_reference, "status": "fulfillment_processing"},
            {"$set": {"status": "fulfillment_pending", "fulfillment_error_code": "internal_fulfillment_error"}},
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
