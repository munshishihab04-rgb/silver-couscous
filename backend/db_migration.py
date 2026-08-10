"""Migrate the CSV-loaded catalog into MongoDB on first boot.
After migration, MongoDB is the source of truth and PRODUCTS list is refreshed
from DB by the server.
"""

from typing import List


async def migrate_products_if_empty(db, seed_products: List[dict]) -> int:
    """If db.products is empty, insert all seed_products. Returns number inserted."""
    count = await db.products.estimated_document_count()
    if count > 0:
        return 0
    if not seed_products:
        return 0
    # Ensure each has a slug (used as _id-like key)
    docs = []
    for p in seed_products:
        d = dict(p)
        d["_id"] = d["slug"]  # deterministic id
        docs.append(d)
    await db.products.insert_many(docs)
    return len(docs)


async def load_products_from_db(db) -> List[dict]:
    """Return all products as plain dicts, without Mongo's _id."""
    out = []
    async for p in db.products.find({}):
        p.pop("_id", None)
        out.append(p)
    return out


async def ensure_default_pages(db):
    """Seed CMS pages if not present."""
    defaults = {
        "privacy":     {"title_it": "Privacy",           "title_en": "Privacy",
                        "content_it": "# Privacy\n\nQuesta pagina è un segnaposto. Inserisci l'informativa dal pannello admin.",
                        "content_en": "# Privacy\n\nThis page is a placeholder. Edit it from the admin panel."},
        "terms":       {"title_it": "Termini",           "title_en": "Terms",
                        "content_it": "# Termini di servizio\n\nSegnaposto — modifica dal pannello admin.",
                        "content_en": "# Terms of Service\n\nPlaceholder — edit from the admin panel."},
        "cookies":     {"title_it": "Cookie",            "title_en": "Cookies",
                        "content_it": "# Cookie policy\n\nSegnaposto — modifica dal pannello admin.",
                        "content_en": "# Cookies policy\n\nPlaceholder — edit from the admin panel."},
        "transparency":{"title_it": "Trasparenza",       "title_en": "Transparency",
                        "content_it": "# Trasparenza\n\nModifica dal pannello admin.",
                        "content_en": "# Transparency\n\nEdit from the admin panel."},
    }
    for slug, doc in defaults.items():
        await db.pages.update_one(
            {"slug": slug},
            {"$setOnInsert": {"slug": slug, **doc}},
            upsert=True,
        )


DEFAULT_SETTINGS = {
    "key": "site",
    "logo_text": "LicenzPøl",
    "logo_url": "",
    "site_title": "LicenzPol — Il software giusto, senza fatica",
    "site_description": "Sistemi operativi, Office, suite creative, CAD, sicurezza e strumenti aziendali. Consegna via email, fattura UE, assistenza in italiano.",
    "primary_email": "support@licenzpol.example",
    "ga4_measurement_id": "",
    "gtm_container_id": "",
    "meta_pixel_id": "",
    "custom_head_html": "",
    "custom_body_html": "",
    "demo_banner": True,
}


async def ensure_default_settings(db):
    existing = await db.settings.find_one({"key": "site"})
    if not existing:
        await db.settings.insert_one(dict(DEFAULT_SETTINGS))
    else:
        # ensure any new default keys are present without overwriting existing values
        missing = {k: v for k, v in DEFAULT_SETTINGS.items() if k not in existing}
        if missing:
            await db.settings.update_one({"key": "site"}, {"$set": missing})
