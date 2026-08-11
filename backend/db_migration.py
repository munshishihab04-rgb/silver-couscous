"""Migrate the CSV-loaded catalog into MongoDB on first boot.
After migration, MongoDB is the source of truth and PRODUCTS list is refreshed
from DB by the server.

This module also handles idempotent backfilling of merchant fields onto legacy
product documents that predate the merchant-authoritative schema.
"""

from datetime import datetime, timezone
from copy import deepcopy
from typing import List

from legal_content import LEGAL_PAGES

MERCHANT_FIELD_DEFAULTS = {
    "sku": None,
    "gtin": None,
    "gtin_status": None,
    "gtin_checksum_status": None,
    "gtin_candidate_private": None,
    "mpn": None,
    "mpn_status": None,
    "mpn_candidate_private": None,
    "condition": "new",
    "selling_price_eur": None,
    "availability_status": "PendingReview",
    "stock": 0,
    "merchant_approved": False,
    "pilot_candidate_private": False,
    "pilot_rank_private": None,
    "catalog_review_status": "not_selected",
    "market_observed_private": False,
    "market_rank_private": None,
    "market_observation_private": None,
    "catalog_visibility_status": "private_review",
    "declared_stock_private": 0,
    "stock_attestation_status_private": None,
    "image_rights_approved": False,
    "image_rights_evidence_private": {},
    "provenance_status": "unverified",
    "provenance_evidence_private": {},
    "status": "draft",
    "google_product_category": None,
    "risk_score": None,
}


async def migrate_products_if_empty(db, seed_products: List[dict]) -> int:
    """If db.products is empty, insert all seed_products. Returns number inserted."""
    count = await db.products.estimated_document_count()
    if count > 0:
        return await reconcile_catalog_products(db, seed_products)
    if not seed_products:
        return 0
    docs = []
    for p in seed_products:
        d = dict(p)
        d["_id"] = d["slug"]
        docs.append(d)
    await db.products.insert_many(docs)
    return len(docs)


def catalog_reconciliation_patch(existing: dict, seed: dict) -> dict:
    """Refresh generated fields while preserving every human-reviewed decision."""
    if existing.get("merchant_approved") is True:
        return {}
    patch = {key: deepcopy(value) for key, value in seed.items() if key != "_id"}
    # Stock is server-inventory state and must never be reset from a catalog seed.
    if "stock" in existing:
        patch["stock"] = existing["stock"]
    if existing.get("merchant_updated_at"):
        reviewed_fields = {
            "selling_price_eur", "stock", "availability_status", "merchant_approved",
            "image_rights_approved", "image_rights_evidence_private",
            "provenance_status", "provenance_evidence_private",
            "gtin", "gtin_status", "mpn", "mpn_status",
            "google_product_category", "status", "admin_notes",
            "catalog_review_status", "catalog_reviewed_at", "catalog_reviewed_by",
            "merchant_updated_at", "merchant_updated_by",
        }
        for key in reviewed_fields:
            if key in existing:
                patch[key] = deepcopy(existing[key])
    return patch


async def reconcile_catalog_products(db, seed_products: List[dict]) -> int:
    """Upsert all draft seed products while preserving human-approved offers."""
    inserted = 0
    for seed in seed_products:
        slug = seed["slug"]
        existing = await db.products.find_one({"slug": slug})
        if existing is None:
            doc = deepcopy(seed)
            doc["_id"] = slug
            await db.products.insert_one(doc)
            inserted += 1
            continue
        patch = catalog_reconciliation_patch(existing, seed)
        if patch:
            await db.products.update_one({"_id": existing["_id"]}, {"$set": patch})
    return inserted


async def backfill_merchant_fields(db, seed_products: List[dict]) -> int:
    """Backfill merchant fields on existing product docs.

    Reads authoritative values from the seed (which comes from catalog.csv) and
    writes them onto existing DB docs ONLY when the field is missing or None.
    Never overwrites human-approved fields like `merchant_approved=True`.
    """
    seed_by_slug = {p["slug"]: p for p in seed_products}
    updated = 0
    async for doc in db.products.find({}):
        slug = doc.get("slug")
        seed = seed_by_slug.get(slug, {})
        patch = {}
        for key, default in MERCHANT_FIELD_DEFAULTS.items():
            if key not in doc:
                patch[key] = seed.get(key, default)
        if patch:
            await db.products.update_one({"_id": doc["_id"]}, {"$set": patch})
            updated += 1
    return updated


async def load_products_from_db(db) -> List[dict]:
    """Return all products as plain dicts, without Mongo's _id."""
    out = []
    async for p in db.products.find({}):
        p.pop("_id", None)
        out.append(p)
    return out


# ---------- Legal / CMS pages -----------------------------------------------


async def ensure_default_pages(db):
    """Keep legal/CMS pages synchronized with the reviewed policy version."""
    now = datetime.now(timezone.utc).isoformat()
    for slug, doc in LEGAL_PAGES.items():
        await db.pages.update_one(
            {"slug": slug},
            {"$set": {"slug": slug, **doc, "updated_at": now}},
            upsert=True,
        )


DEFAULT_SETTINGS = {
    "key": "site",
    "logo_text": "LicenzPøl",
    "logo_url": "",
    "site_title": "LicenzPol — ambiente di pre-lancio",
    "site_description": "Catalogo e checkout in verifica. Nessun pagamento reale è attivo.",
    # Business identity — DIGITALSOFT DI MUNSHI SHIHAB
    "business_legal_name": "DIGITALSOFT DI MUNSHI SHIHAB",
    "business_address": "Via Aldo Pio Manuzio 24, 40132 Bologna (BO)",
    "business_vat": "04358941203",
    "business_rea": "588058",
    "business_email": "supporto@licenzpol.it",
    "business_phone": "+39 393 684 1051",
    "primary_email": "supporto@licenzpol.it",
    "ga4_measurement_id": "",
    "gtm_container_id": "",
    "meta_pixel_id": "",
    "demo_banner": True,  # true in staging/dev, false in production
}


async def ensure_default_settings(db):
    existing = await db.settings.find_one({"key": "site"})
    if not existing:
        await db.settings.insert_one(dict(DEFAULT_SETTINGS))
        return
    missing = {k: v for k, v in DEFAULT_SETTINGS.items() if k not in existing}
    truthful = {
        "logo_text": DEFAULT_SETTINGS["logo_text"],
        "site_title": DEFAULT_SETTINGS["site_title"],
        "site_description": DEFAULT_SETTINGS["site_description"],
        "primary_email": DEFAULT_SETTINGS["primary_email"],
        "demo_banner": True,
    }
    await db.settings.update_one({"key": "site"}, {"$set": {**missing, **truthful}})
