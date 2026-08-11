"""Merchant approval workflow + license inventory admin endpoints.

Mounted at /api/admin/merchant/*.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from pydantic import BaseModel, Field

from auth import current_admin
from services import license_inventory


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

    # No GTIN → risky
    gtin_ok = bool(p.get("gtin")) and (p.get("gtin_status") == "valid")
    if not gtin_ok:
        score += 25
        reasons.append("gtin missing or invalid")

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
            ref = min(v.get("price_eur", 0) for v in variants if v.get("price_eur"))
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


# ---------- Merchant workflow endpoints ------------------------------------

class ApprovalPatch(BaseModel):
    merchant_approved: Optional[bool] = None
    image_rights_approved: Optional[bool] = None
    provenance_status: Optional[str] = None  # unverified | pending | verified
    selling_price_eur: Optional[float] = None
    stock: Optional[int] = None
    sku: Optional[str] = None
    gtin: Optional[str] = None
    mpn: Optional[str] = None
    google_product_category: Optional[str] = None
    status: Optional[str] = None
    admin_notes: Optional[str] = None


@merchant_admin_router.get("/queue")
async def merchant_queue(
    request: Request,
    only_approved: bool = False,
    only_pending: bool = False,
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
    items.sort(key=lambda x: (x.get("merchant_approved", False), x["_risk"]["score"]))
    return {"total": len(items), "approved_count": approved_count, "items": items}


@merchant_admin_router.patch("/products/{slug}")
async def merchant_patch(
    slug: str,
    body: ApprovalPatch,
    request: Request,
    user=Depends(current_admin),
):
    db = _db(request)
    update = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="Nessun campo da aggiornare.")
    update["merchant_updated_at"] = datetime.now(timezone.utc).isoformat()
    update["merchant_updated_by"] = user.get("email", user["_id"])
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
    if is_production():
        from publication import is_public_offer
        async for product in db.products.find({"merchant_approved": True}):
            if is_public_offer(product):
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
    }
