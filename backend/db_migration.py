"""Migrate the CSV-loaded catalog into MongoDB on first boot.
After migration, MongoDB is the source of truth and PRODUCTS list is refreshed
from DB by the server.

This module also handles idempotent backfilling of merchant fields onto legacy
product documents that predate the merchant-authoritative schema.
"""

from datetime import datetime, timezone
from typing import List

from legal_content import LEGAL_PAGES

MERCHANT_FIELD_DEFAULTS = {
    "sku": None,
    "gtin": None,
    "gtin_status": None,
    "mpn": None,
    "condition": "new",
    "selling_price_eur": None,
    "availability_status": "PendingReview",
    "stock": 0,
    "merchant_approved": False,
    "image_rights_approved": False,
    "provenance_status": "unverified",
    "status": "draft",
    "google_product_category": None,
    "risk_score": None,
}


async def migrate_products_if_empty(db, seed_products: List[dict]) -> int:
    """If db.products is empty, insert all seed_products. Returns number inserted."""
    count = await db.products.estimated_document_count()
    if count > 0:
        # DB already populated — backfill merchant fields idempotently.
        await backfill_merchant_fields(db, seed_products)
        return 0
    if not seed_products:
        return 0
    docs = []
    for p in seed_products:
        d = dict(p)
        d["_id"] = d["slug"]
        docs.append(d)
    await db.products.insert_many(docs)
    return len(docs)


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
