"""Merchant approval workflow + license inventory admin endpoints.

Mounted at /api/admin/merchant/*.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from pydantic import BaseModel, Field

from auth import current_admin
from services import license_inventory
from publication import offer_gate_failures
from pilot_catalog import catalog_review_blockers
from evidence import bind_image_fingerprint, image_rights_evidence_verified, provenance_evidence_verified


merchant_admin_router = APIRouter(prefix="/api/admin/merchant")


def _db(req: Request):
    return req.app.state.db


def _reload(req: Request):
    if hasattr(req.app.state, "reload_products"):
        return req.app.state.reload_products()


# ---------- Risk scoring ---------------------------------------------------

def compute_risk_score(p: dict) -> dict:
    """Heuristic 0..100 risk score for auto-suggesting products for approval.

    Lower is better. Products that end up around ≤30 are considered low-risk.
    """
    score = 0
    reasons = []

    # An identifier is acceptable only after assignment evidence is approved.
    gtin_ok = bool(p.get("gtin")) and (p.get("gtin_status") == "verified")
    mpn_ok = bool(p.get("mpn")) and (p.get("mpn_status") == "verified")
    if not (gtin_ok or mpn_ok):
        score += 25
        reasons.append("product identifier assignment not verified")

    # No SKU → risky
    if not p.get("sku"):
        score += 20
        reasons.append("sku missing")

    # No selling price → high risk
    if not p.get("selling_price_eur"):
        score += 30
        reasons.append("selling_price missing")

    # Extreme discount ratio (reference vs selling) → suspicious
    ref = None
    variants = p.get("variants") or []
    if variants:
        try:
            ref = min(v.get("reference_price_private", 0) for v in variants if v.get("reference_price_private"))
        except Exception:
            ref = None
    sell = p.get("selling_price_eur")
    if ref and sell and ref > 0:
        ratio = sell / ref
        if ratio < 0.3:
            score += 15
            reasons.append("selling_price <30% of reference — suspicious")
        elif ratio > 3:
            score += 10
            reasons.append("selling_price >3x reference — check")

    # No image or unowned image → risky
    if not p.get("image_url"):
        score += 10
        reasons.append("no image")
    if not p.get("image_rights_approved"):
        score += 10
        reasons.append("image rights not yet documented")
    elif not image_rights_evidence_verified(p.get("image_rights_evidence_private")):
        score += 15
        reasons.append("image rights flag has no valid evidence record")
    if p.get("provenance_status") != "verified" or not provenance_evidence_verified(p.get("provenance_evidence_private")):
        score += 15
        reasons.append("commercial provenance not documented")
    if p.get("catalog_review_status") != "approved":
        score += 10
        reasons.append("pilot catalog review not approved")

    # Brand reputation (basic heuristic)
    brand = (p.get("brand") or "").lower()
    if brand in {"microsoft", "adobe", "autodesk", "corel", "kaspersky", "bitdefender"}:
        score -= 5

    # Availability status
    avail = (p.get("availability_status") or "").lower()
    if avail == "instock":
        score -= 3

    score = max(0, min(100, score))
    return {"score": score, "reasons": reasons}


def approval_blockers(existing: dict, update: dict) -> list[str]:
    proposed = {**existing, **update}
    if update.get("merchant_approved") is True:
        proposed["status"] = update.get("status", "approved")
    return offer_gate_failures(proposed)


def evidence_update_blockers(existing: dict, update: dict) -> list[str]:
    proposed = {**existing, **update}
    blockers = []
    if update.get("provenance_status") == "verified" and not provenance_evidence_verified(
        proposed.get("provenance_evidence_private")
    ):
        blockers.append("provenance_evidence_invalid")
    if update.get("image_rights_approved") is True and not image_rights_evidence_verified(
        proposed.get("image_rights_evidence_private")
    ):
        blockers.append("image_rights_evidence_invalid")
    return blockers


def catalog_review_update_blockers(existing: dict, update: dict) -> list[str]:
    if update.get("catalog_review_status") != "approved":
        return []
    if existing.get("pilot_candidate_private") is not True:
        return ["pilot_not_selected"]
    return catalog_review_blockers({**existing, **update})


# ---------- Merchant workflow endpoints ------------------------------------

class ApprovalPatch(BaseModel):
    merchant_approved: Optional[bool] = None
    catalog_review_status: Optional[str] = None  # pending | approved | rejected
    image_rights_approved: Optional[bool] = None
    image_rights_evidence_private: Optional[dict] = None
    provenance_status: Optional[str] = None  # unverified | pending | verified
    provenance_evidence_private: Optional[dict] = None
    selling_price_eur: Optional[float] = None
    stock: Optional[int] = None
    sku: Optional[str] = None
    gtin: Optional[str] = None
    gtin_status: Optional[str] = None
    mpn: Optional[str] = None
    mpn_status: Optional[str] = None
    availability_status: Optional[str] = None
    condition: Optional[str] = None
    google_product_category: Optional[str] = None
    status: Optional[str] = None
    admin_notes: Optional[str] = None


@merchant_admin_router.get("/queue")
async def merchant_queue(
    request: Request,
    only_approved: bool = False,
    only_pending: bool = False,
    pilot_only: bool = False,
    market_only: bool = False,
    max_risk: Optional[int] = None,
    limit: int = 500,
    user=Depends(current_admin),
):
    db = _db(request)
    q = {}
    if only_approved:
        q["merchant_approved"] = True
    if only_pending:
        q["merchant_approved"] = False
    if pilot_only:
        q["pilot_candidate_private"] = True
    if market_only:
        q["market_observed_private"] = True
    items = []
    approved_count = 0
    async for p in db.products.find(q).limit(limit):
        p.pop("_id", None)
        risk = compute_risk_score(p)
        available_keys = await license_inventory.available_count(db, p.get("sku") or "")
        p["_risk"] = risk
        p["_available_keys"] = available_keys
        if max_risk is not None and risk["score"] > max_risk:
            continue
        if p.get("merchant_approved"):
            approved_count += 1
        items.append(p)
    items.sort(key=lambda x: (
        not x.get("market_observed_private", False),
        x.get("market_rank_private") or 9999,
        not x.get("pilot_candidate_private", False),
        x.get("pilot_rank_private") or 9999,
        x.get("merchant_approved", False),
        x["_risk"]["score"],
    ))
    return {"total": len(items), "approved_count": approved_count, "items": items}


@merchant_admin_router.patch("/products/{slug}")
async def merchant_patch(
    slug: str,
    body: ApprovalPatch,
    request: Request,
    user=Depends(current_admin),
):
    db = _db(request)
    existing = await db.products.find_one({"slug": slug})
    if existing is None:
        raise HTTPException(status_code=404, detail="Prodotto non trovato.")
    update = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="Nessun campo da aggiornare.")
    review_time = datetime.now(timezone.utc).isoformat()
    actor = user.get("email", user["_id"])
    if isinstance(update.get("image_rights_evidence_private"), dict):
        update["image_rights_evidence_private"] = bind_image_fingerprint(
            existing.get("image_rights_evidence_private"),
            update["image_rights_evidence_private"],
        )
        if "image_rights_approved" in update:
            update["image_rights_evidence_private"]["status"] = "approved" if update["image_rights_approved"] else "unverified"
    if isinstance(update.get("provenance_evidence_private"), dict) and "provenance_status" in update:
        update["provenance_evidence_private"]["status"] = update["provenance_status"]
    for evidence_key in ("provenance_evidence_private", "image_rights_evidence_private"):
        if isinstance(update.get(evidence_key), dict):
            update[evidence_key] = {
                **update[evidence_key],
                "reviewed_by": actor,
                "reviewed_at": review_time,
            }
    evidence_blockers = evidence_update_blockers(existing, update)
    if evidence_blockers:
        raise HTTPException(status_code=400, detail={"code": "evidence_invalid", "blockers": evidence_blockers})
    review_blockers = catalog_review_update_blockers(existing, update)
    if review_blockers:
        raise HTTPException(status_code=400, detail={"code": "catalog_review_blocked", "blockers": review_blockers})
    if update.get("catalog_review_status") == "approved":
        update["catalog_reviewed_at"] = review_time
        update["catalog_reviewed_by"] = actor
    if update.get("merchant_approved") is True:
        blockers = approval_blockers(existing, update)
        if blockers:
            raise HTTPException(status_code=400, detail={"code": "publication_blocked", "blockers": blockers})
    update["merchant_updated_at"] = review_time
    update["merchant_updated_by"] = actor
    # Auto-status
    if update.get("merchant_approved"):
        update.setdefault("status", "approved")
    res = await db.products.update_one({"slug": slug}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Prodotto non trovato.")
    # Audit log
    await db.merchant_audit.insert_one({
        "slug": slug, "actor": user.get("email"),
        "changes": update,
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    await _reload(request)
    doc = await db.products.find_one({"slug": slug})
    doc.pop("_id", None)
    return doc


class BulkApproveBody(BaseModel):
    slugs: List[str]
    merchant_approved: bool = True
    image_rights_approved: Optional[bool] = None


@merchant_admin_router.post("/bulk-approve")
async def merchant_bulk_approve(
    body: BulkApproveBody, request: Request, user=Depends(current_admin),
):
    db = _db(request)
    if body.merchant_approved:
        proposed = {"merchant_approved": True, "status": "approved"}
        if body.image_rights_approved is not None:
            proposed["image_rights_approved"] = body.image_rights_approved
        blocked = {}
        async for product in db.products.find({"slug": {"$in": body.slugs}}):
            reasons = approval_blockers(product, proposed)
            if reasons:
                blocked[product["slug"]] = reasons
        if blocked:
            raise HTTPException(status_code=400, detail={"code": "bulk_publication_blocked", "products": blocked})
    update = {
        "merchant_approved": body.merchant_approved,
        "status": "approved" if body.merchant_approved else "draft",
        "merchant_updated_at": datetime.now(timezone.utc).isoformat(),
        "merchant_updated_by": user.get("email", user["_id"]),
    }
    if body.image_rights_approved is not None:
        update["image_rights_approved"] = body.image_rights_approved
    res = await db.products.update_many({"slug": {"$in": body.slugs}}, {"$set": update})
    await db.merchant_audit.insert_one({
        "slugs": body.slugs, "actor": user.get("email"),
        "changes": update, "bulk": True,
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    await _reload(request)
    return {"matched": res.matched_count, "modified": res.modified_count}


# ---------- License inventory ----------------------------------------------

class LicenseImportBody(BaseModel):
    sku: str
    keys: List[str]
    source: str = "manual"


@merchant_admin_router.post("/licenses/import")
async def merchant_import_licenses(
    body: LicenseImportBody, request: Request, user=Depends(current_admin),
):
    db = _db(request)
    added = await license_inventory.import_keys(db, body.sku, body.keys, source=body.source)
    # sync stock on all products with that SKU
    n_avail = await license_inventory.available_count(db, body.sku)
    await db.products.update_many({"sku": body.sku}, {"$set": {"stock": n_avail}})
    await _reload(request)
    return {"imported": added, "available_now": n_avail}


@merchant_admin_router.get("/licenses/{sku}")
async def merchant_license_status(sku: str, request: Request, user=Depends(current_admin)):
    db = _db(request)
    counts = {"available": 0, "reserved": 0, "delivered": 0, "released": 0}
    async for c in db.license_keys.aggregate([
        {"$match": {"sku": sku}},
        {"$group": {"_id": "$status", "n": {"$sum": 1}}},
    ]):
        counts[c["_id"]] = c["n"]
    return {"sku": sku, **counts, "total": sum(counts.values())}


# ---------- Merchant environment/status ------------------------------------

@merchant_admin_router.get("/status")
async def merchant_status(request: Request, user=Depends(current_admin)):
    from config import APP_ENV, COMMERCE_ENABLED, PUBLIC_SITE_URL, is_production
    from nexi_xpay import is_configured as nexi_configured
    from config import BREVO_API_KEY
    db = _db(request)
    approved = await db.products.count_documents({"merchant_approved": True})
    feedable = 0
    provenance_verified = 0
    image_rights_verified = 0
    pilot_candidates = 0
    catalog_review_approved = 0
    market_previews = 0
    declared_stock_total = 0
    async for product in db.products.find({}):
        if product.get("market_observed_private") is True:
            market_previews += 1
            declared_stock_total += int(product.get("declared_stock_private") or 0)
        if product.get("pilot_candidate_private") is True:
            pilot_candidates += 1
        if product.get("catalog_review_status") == "approved":
            catalog_review_approved += 1
        if provenance_evidence_verified(product.get("provenance_evidence_private")):
            provenance_verified += 1
        if image_rights_evidence_verified(product.get("image_rights_evidence_private")):
            image_rights_verified += 1
        if is_production() and product.get("merchant_approved") and not offer_gate_failures(product):
            feedable += 1
    return {
        "app_env": APP_ENV,
        "commerce_enabled": COMMERCE_ENABLED,
        "public_site_url": PUBLIC_SITE_URL,
        "is_production": is_production(),
        "psp_configured": nexi_configured(),
        "email_configured": bool(BREVO_API_KEY),
        "approved_products": approved,
        "feedable_products": feedable,
        "pilot_candidates": pilot_candidates,
        "catalog_review_approved": catalog_review_approved,
        "market_previews": market_previews,
        "declared_stock_total": declared_stock_total,
        "provenance_evidence_verified": provenance_verified,
        "image_rights_evidence_verified": image_rights_verified,
    }
