from fastapi import FastAPI, APIRouter, HTTPException, Request, Body
from dotenv import load_dotenv
from pathlib import Path
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from catalog import PRODUCTS as _CSV_PRODUCTS, CATEGORIES, NEEDS
from families import FAMILIES, get_family
from auth import seed_admin, ensure_indexes
from db_migration import migrate_products_if_empty, load_products_from_db, ensure_default_pages, ensure_default_settings
from admin_routes import admin_router
from exports_seo import exports_router, seo_router
from merchant_feed import merchant_router
from merchant_admin import merchant_admin_router
from payments import payments_router
from config import (
    APP_ENV, COMMERCE_ENABLED, cors_origins,
    validate_production_startup, is_production,
)
from services import license_inventory
from privacy import prepare_analytics_event


BUNDLE_TIERS = [
    {"min_items": 2, "discount": 0.08},
    {"min_items": 3, "discount": 0.12},
    {"min_items": 4, "discount": 0.15},
]

BUNDLE_SLOTS = [
    {"key": "os",       "required": True,  "categories": ["os"],
     "title_it": "Sistema operativo", "title_en": "Operating System",
     "hint_it": "La base per il tuo PC.", "hint_en": "The base of your PC."},
    {"key": "office",   "required": True,  "categories": ["office"],
     "title_it": "Produttività",      "title_en": "Productivity",
     "hint_it": "Documenti, fogli, presentazioni.", "hint_en": "Docs, sheets, decks."},
    {"key": "security", "required": True,  "categories": ["security"],
     "title_it": "Sicurezza",         "title_en": "Security",
     "hint_it": "Un livello di protezione essenziale.", "hint_en": "An essential layer of protection."},
    {"key": "creative", "required": False, "categories": ["creative"],
     "title_it": "Creatività (opzionale)", "title_en": "Creative (optional)",
     "hint_it": "Foto, video, illustrazione.", "hint_en": "Photo, video, illustration."},
    {"key": "utility",  "required": False, "categories": ["utility", "business"],
     "title_it": "Extra (opzionale)",     "title_en": "Extras (optional)",
     "hint_it": "Utility e strumenti aggiuntivi.", "hint_en": "Utilities and extra tools."},
]


def compute_bundle_discount(n_items: int) -> float:
    d = 0.0
    for t in BUNDLE_TIERS:
        if n_items >= t["min_items"]:
            d = t["discount"]
    return d


class BundleSelection(BaseModel):
    product_slug: str
    variant_id: str


class BundlePreviewRequest(BaseModel):
    selections: List[BundleSelection]


ROOT_DIR = Path(__file__).parent  # already imported

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="LicenzPol API")
app.state.db = db
api_router = APIRouter(prefix="/api")

# In-memory mirror of MongoDB products for fast filtering.
PRODUCTS: List[dict] = list(_CSV_PRODUCTS)


def get_product_by_slug(slug: str):
    for p in PRODUCTS:
        if p["slug"] == slug:
            return p
    return None


async def _reload_products():
    """Refresh the in-memory PRODUCTS list from MongoDB."""
    global PRODUCTS
    PRODUCTS = await load_products_from_db(db)


app.state.reload_products = _reload_products


@app.on_event("startup")
async def _startup():
    # Fail-closed guard in production
    missing = validate_production_startup()
    if missing:
        raise RuntimeError(
            "Production startup aborted: missing settings: " + ", ".join(missing)
        )
    logging.info(f"[startup] APP_ENV={APP_ENV}  COMMERCE_ENABLED={COMMERCE_ENABLED}")
    await ensure_indexes(db)
    await license_inventory.ensure_indexes(db)
    await seed_admin(db)
    inserted = await migrate_products_if_empty(db, _CSV_PRODUCTS)
    if inserted:
        logging.info(f"[startup] migrated {inserted} products from CSV into MongoDB")
    await ensure_default_pages(db)
    await ensure_default_settings(db)
    await _reload_products()
    logging.info(f"[startup] products in DB: {len(PRODUCTS)}")


class OrderLineItem(BaseModel):
    product_slug: str
    variant_id: str
    quantity: int = 1


class ConsentBlock(BaseModel):
    accept_terms: bool = False
    immediate_delivery_consent: bool = False  # loses right of withdrawal
    consent_version: str = "2026-08-11"


class OrderCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    country: str
    company: Optional[str] = None
    vat: Optional[str] = None
    items: List[OrderLineItem]
    language: str = "it"
    consent: ConsentBlock = Field(default_factory=ConsentBlock)
    idempotency_key: Optional[str] = None


class OrderResponse(BaseModel):
    id: str
    reference: str
    created_at: str
    status: str
    demo: bool
    total_eur: float


class SupportMessage(BaseModel):
    email: str
    subject: str
    message: str
    language: str = "it"


@api_router.get("/")
async def root():
    return {"service": "LicenzPol", "status": "ok"}


@api_router.get("/categories")
async def list_categories():
    return CATEGORIES


@api_router.get("/needs")
async def list_needs():
    return NEEDS


@api_router.get("/products")
async def list_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    platform: Optional[str] = None,
    brand: Optional[str] = None,
    license_type: Optional[str] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    need: Optional[str] = None,
    sort: Optional[str] = "featured",
    limit: Optional[int] = 500,
):
    items = list(PRODUCTS)
    if q:
        needle = q.lower().strip()
        items = [p for p in items if needle in p["name"].lower()
                 or needle in p["brand"].lower()
                 or needle in p["tagline_it"].lower()
                 or needle in p["tagline_en"].lower()]
    if category:
        items = [p for p in items if p["category"] == category]
    if platform:
        items = [p for p in items if platform in p["platforms"]]
    if brand:
        items = [p for p in items if p["brand"].lower() == brand.lower()]
    if license_type:
        items = [p for p in items if p["licenseType"].lower() == license_type.lower()]
    if need:
        target_cats = next((n["categories"] for n in NEEDS if n["key"] == need), [])
        if target_cats:
            items = [p for p in items if p["category"] in target_cats]

    def base_price(p):
        return min(v["price_eur"] for v in p["variants"]) if p["variants"] else 0

    if min_price is not None:
        items = [p for p in items if base_price(p) >= min_price]
    if max_price is not None:
        items = [p for p in items if base_price(p) <= max_price]

    if sort == "price_asc":
        items.sort(key=base_price)
    elif sort == "price_desc":
        items.sort(key=base_price, reverse=True)
    elif sort == "name":
        items.sort(key=lambda p: p["name"])

    return {"total": len(items), "items": items[:limit]}


@api_router.get("/products/{slug}")
async def get_product(slug: str):
    p = get_product_by_slug(slug)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


@api_router.get("/related/{slug}")
async def related_products(slug: str, limit: int = 4):
    p = get_product_by_slug(slug)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    same_cat = [x for x in PRODUCTS if x["category"] == p["category"] and x["slug"] != slug]
    same_cat.sort(key=lambda x: min(v["price_eur"] for v in x["variants"]))
    return same_cat[:limit]


def _match_family_products(family):
    m = family.get("match", {})
    items = list(PRODUCTS)
    if family.get("brand"):
        items = [p for p in items if p["brand"].lower() == family["brand"].lower()]
    if m.get("category"):
        items = [p for p in items if p["category"] == m["category"]]
    return items


def _group_products(products, group_by: str):
    """Return an ordered list of {key, label_it, label_en, items[]}."""
    import re as _re
    buckets = {}
    order = []

    def bucket(key, label_it, label_en):
        if key not in buckets:
            buckets[key] = {"key": key, "label_it": label_it, "label_en": label_en, "items": []}
            order.append(key)
        return buckets[key]

    for p in products:
        n = p["name"].upper()
        if group_by == "windows_version":
            m = _re.search(r"WINDOWS\s+(SERVER\s+\d{4}|\d+)", n)
            if m:
                v = m.group(1).replace("  ", " ").strip()
                key = f"windows-{v.lower().replace(' ', '-')}"
                label = f"Windows {v.title()}" if not v.startswith("SERVER") else f"Windows {v.title()}"
                bucket(key, label, label)["items"].append(p)
            else:
                bucket("other", "Altri", "Others")["items"].append(p)
        elif group_by == "office_year":
            if "365" in n:
                bucket("m365", "Microsoft 365", "Microsoft 365")["items"].append(p)
                continue
            m = _re.search(r"OFFICE\s+(20\d{2})", n)
            if m:
                y = m.group(1)
                bucket(f"office-{y}", f"Office {y}", f"Office {y}")["items"].append(p)
                continue
            # Individual apps
            for app in ["VISIO", "PROJECT", "ACCESS", "WORD", "EXCEL", "POWERPOINT", "OUTLOOK", "ONENOTE", "PUBLISHER"]:
                if app in n:
                    lbl = app.title()
                    bucket(f"app-{app.lower()}", lbl, lbl)["items"].append(p)
                    break
            else:
                bucket("other", "Altri", "Others")["items"].append(p)
        elif group_by == "adobe_app":
            for app, lbl in [
                ("CREATIVE CLOUD", "Creative Cloud"), ("PHOTOSHOP", "Photoshop"),
                ("ILLUSTRATOR", "Illustrator"), ("INDESIGN", "InDesign"),
                ("PREMIERE", "Premiere Pro"), ("AFTER EFFECTS", "After Effects"),
                ("LIGHTROOM", "Lightroom"), ("ACROBAT", "Acrobat"),
                ("AUDITION", "Audition"), ("ANIMATE", "Animate"),
                ("DREAMWEAVER", "Dreamweaver"), ("XD", "Adobe XD"),
                ("BRIDGE", "Bridge"),
            ]:
                if app in n:
                    bucket(f"adobe-{lbl.lower().replace(' ', '-')}", lbl, lbl)["items"].append(p)
                    break
            else:
                bucket("other", "Altri strumenti", "Other tools")["items"].append(p)
        elif group_by == "autodesk_product":
            for app, lbl in [
                ("AUTOCAD LT", "AutoCAD LT"), ("AUTOCAD", "AutoCAD"),
                ("REVIT", "Revit"), ("3DS MAX", "3ds Max"), ("MAYA", "Maya"),
                ("INVENTOR", "Inventor"), ("FUSION", "Fusion"),
                ("NAVISWORKS", "Navisworks"), ("CIVIL 3D", "Civil 3D"),
                ("ARCHITECTURE", "Architecture"),
            ]:
                if app in n:
                    bucket(f"autodesk-{lbl.lower().replace(' ', '-')}", lbl, lbl)["items"].append(p)
                    break
            else:
                bucket("other", "Altri strumenti", "Other tools")["items"].append(p)
        else:
            bucket("all", "Tutti", "All")["items"].append(p)

    # Sort groups: newest / most recognisable first — use natural sort
    def sort_key(k):
        m = _re.search(r"(\d+)", k)
        return -int(m.group(1)) if m else 0

    order.sort(key=sort_key)
    # Sort items inside each group by price ascending
    result = []
    for k in order:
        b = buckets[k]
        b["items"].sort(key=lambda p: p["variants"][0]["price_eur"])
        result.append(b)
    return result


@api_router.get("/families")
async def list_families():
    out = []
    for f in FAMILIES:
        items = _match_family_products(f)
        out.append({**{k: v for k, v in f.items() if k != "match"}, "product_count": len(items)})
    return out


@api_router.get("/families/{slug}")
async def get_family_detail(slug: str):
    f = get_family(slug)
    if not f:
        raise HTTPException(status_code=404, detail="Family not found")
    items = _match_family_products(f)
    groups = _group_products(items, f.get("group_by", "all"))
    featured = sorted(items, key=lambda p: p["variants"][0]["price_eur"])[:4]
    return {
        **{k: v for k, v in f.items() if k != "match"},
        "product_count": len(items),
        "featured": featured,
        "groups": groups,
    }


@api_router.post("/orders/quote")
async def orders_quote(payload: dict = Body(...)):
    """Server-side quote: recompute totals to validate the client cart.

    Body: { items: [{ product_slug, variant_id, quantity }] }
    """
    items = payload.get("items") or []
    resolved = []
    subtotal = 0.0
    unavailable = []
    for line in items:
        slug = line.get("product_slug")
        vid = line.get("variant_id")
        qty = max(1, int(line.get("quantity") or 1))
        p = get_product_by_slug(slug)
        if not p:
            unavailable.append({"product_slug": slug, "reason": "not_found"})
            continue
        if is_production() and not p.get("merchant_approved"):
            unavailable.append({"product_slug": slug, "reason": "not_approved"})
            continue
        v = next((x for x in p["variants"] if x["id"] == vid), None)
        if not v:
            unavailable.append({"product_slug": slug, "reason": "variant_not_found"})
            continue
        unit = p.get("selling_price_eur") or v["price_eur"]
        line_total = round(unit * qty, 2)
        subtotal += line_total
        resolved.append({
            "product_slug": p["slug"], "product_name": p["name"],
            "variant_id": v["id"], "quantity": qty,
            "unit_price_eur": round(unit, 2), "line_total_eur": line_total,
            "sku": p.get("sku"),
        })
    return {
        "items": resolved,
        "unavailable": unavailable,
        "subtotal_eur": round(subtotal, 2),
        "total_eur": round(subtotal, 2),
        "currency": "EUR",
        "commerce_enabled": COMMERCE_ENABLED,
    }


@api_router.post("/orders", response_model=OrderResponse)
async def create_order(order: OrderCreate):
    # ---- Server-authoritative validation ----
    if not order.consent.accept_terms:
        raise HTTPException(status_code=400, detail="Devi accettare i Termini di vendita.")

    # Idempotency: if a key was provided and we already have an order for it, return it.
    if order.idempotency_key:
        existing = await db.orders.find_one({"idempotency_key": order.idempotency_key})
        if existing:
            return OrderResponse(
                id=existing["id"], reference=existing["reference"],
                created_at=existing["created_at"], status=existing["status"],
                demo=existing.get("demo", True), total_eur=existing["total_eur"],
            )

    # Recompute totals from the server-side catalog. Reject unknown / not-for-sale items.
    resolved_items = []
    subtotal = 0.0
    for line in order.items:
        p = get_product_by_slug(line.product_slug)
        if not p:
            raise HTTPException(status_code=400, detail=f"Prodotto {line.product_slug} non trovato.")
        # In production only merchant_approved products can be purchased.
        if is_production() and not p.get("merchant_approved"):
            raise HTTPException(status_code=400, detail=f"Prodotto {line.product_slug} non disponibile.")
        v = next((x for x in p["variants"] if x["id"] == line.variant_id), None)
        if not v:
            raise HTTPException(status_code=400, detail=f"Variante {line.variant_id} non trovata.")
        qty = max(1, int(line.quantity or 1))
        # Prefer authoritative selling_price_eur, fall back to variant price for legacy demo
        unit = p.get("selling_price_eur") or v["price_eur"]
        line_total = round(unit * qty, 2)
        subtotal += line_total
        resolved_items.append({
            "product_slug": p["slug"],
            "product_name": p["name"],
            "variant_id": v["id"],
            "variant_label": f"{v['edition']} · {'Perpetua' if v['duration_months'] == 0 else str(v['duration_months']) + 'm'} · {v['devices']}pc",
            "quantity": qty,
            "unit_price_eur": round(unit, 2),
            "sku": p.get("sku"),
        })

    total = round(subtotal, 2)
    ref = "LP-" + uuid.uuid4().hex[:8].upper()

    demo = not COMMERCE_ENABLED
    initial_status = "demo_confirmed" if demo else "pending_payment"

    doc = {
        "id": str(uuid.uuid4()),
        "reference": ref,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": initial_status,
        "demo": demo,
        "email": order.email,
        "first_name": order.first_name,
        "last_name": order.last_name,
        "country": order.country,
        "company": order.company,
        "vat": order.vat,
        "language": order.language,
        "items": resolved_items,
        "subtotal_eur": round(subtotal, 2),
        "total_eur": total,
        "consent": order.consent.model_dump(),
        "idempotency_key": order.idempotency_key,
    }
    await db.orders.insert_one(doc)
    return OrderResponse(
        id=doc["id"], reference=ref, created_at=doc["created_at"],
        status=initial_status, demo=demo, total_eur=total,
    )


@api_router.get("/orders/{reference}", response_model=OrderResponse)
async def get_order(reference: str):
    doc = await db.orders.find_one({"reference": reference}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(
        id=doc["id"], reference=doc["reference"],
        created_at=doc["created_at"], status=doc["status"],
        demo=doc.get("demo", True), total_eur=doc["total_eur"],
    )


@api_router.post("/support")
async def create_support_message(msg: SupportMessage):
    doc = {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        **msg.model_dump(),
    }
    await db.support_messages.insert_one(doc)
    return {"ok": True, "id": doc["id"]}


@api_router.get("/bundle/config")
async def bundle_config():
    return {"slots": BUNDLE_SLOTS, "tiers": BUNDLE_TIERS}


@api_router.get("/bundle/preset/nuovo-pc")
async def bundle_preset_nuovo_pc():
    """A curated 'Nuovo PC' preset: cheapest recent OS + Office + Security."""
    from catalog import PRODUCTS as _P

    def pick_by(pred):
        candidates = [p for p in _P if pred(p)]
        if not candidates:
            return None
        candidates.sort(key=lambda p: p["variants"][0]["price_eur"])
        return candidates[0]

    picks = []
    # Prefer Windows 11 Pro; fall back to any Windows OS
    os_pick = pick_by(lambda p: p["category"] == "os" and "windows 11" in p["name"].lower() and "pro" in p["name"].lower()) \
              or pick_by(lambda p: p["category"] == "os" and "windows 11" in p["name"].lower()) \
              or pick_by(lambda p: p["category"] == "os")
    # Prefer recent Office Pro; fall back to any Office
    office_pick = pick_by(lambda p: p["category"] == "office" and "office 2021" in p["name"].lower() and "professional" in p["name"].lower()) \
                  or pick_by(lambda p: p["category"] == "office" and "office 2021" in p["name"].lower()) \
                  or pick_by(lambda p: p["category"] == "office" and "office 2019" in p["name"].lower() and "professional" in p["name"].lower()) \
                  or pick_by(lambda p: p["category"] == "office")
    # Any security product
    sec_pick = pick_by(lambda p: p["category"] == "security")

    for prod in [os_pick, office_pick, sec_pick]:
        if prod:
            picks.append({"product_slug": prod["slug"], "variant_id": prod["variants"][0]["id"]})
    return {"selections": picks}


@api_router.post("/bundle/preview")
async def bundle_preview(req: BundlePreviewRequest):
    lines = []
    subtotal = 0.0
    for sel in req.selections:
        p = get_product_by_slug(sel.product_slug)
        if not p:
            continue
        v = next((x for x in p["variants"] if x["id"] == sel.variant_id), None)
        if not v:
            continue
        subtotal += v["price_eur"]
        lines.append({
            "product_slug": p["slug"], "product_name": p["name"],
            "brand": p["brand"], "mark": p["mark"], "colorKey": p["colorKey"],
            "category": p["category"],
            "variant_id": v["id"], "edition": v["edition"],
            "duration_months": v["duration_months"], "devices": v["devices"],
            "price_eur": v["price_eur"],
        })
    discount_pct = compute_bundle_discount(len(lines))
    discount_eur = round(subtotal * discount_pct, 2)
    total = round(subtotal - discount_eur, 2)
    return {
        "items": lines,
        "count": len(lines),
        "subtotal_eur": round(subtotal, 2),
        "discount_pct": discount_pct,
        "discount_eur": discount_eur,
        "total_eur": total,
    }


app.include_router(api_router)
app.include_router(admin_router)
app.include_router(exports_router)
app.include_router(seo_router)
app.include_router(merchant_router)
app.include_router(merchant_admin_router)
app.include_router(payments_router)


# ---------- Public settings, CMS pages and analytics ------------------------

PUBLIC_SETTINGS_FIELDS = {
    "logo_text", "logo_url", "site_title", "site_description",
    "primary_email", "ga4_measurement_id", "gtm_container_id", "meta_pixel_id",
    "demo_banner",
}


@app.get("/api/settings")
async def public_settings():
    s = await db.settings.find_one({"key": "site"}) or {}
    return {k: s.get(k) for k in PUBLIC_SETTINGS_FIELDS}


@app.get("/api/pages/{slug}")
async def public_page(slug: str):
    p = await db.pages.find_one({"slug": slug})
    if not p:
        raise HTTPException(status_code=404, detail="Page not found")
    p.pop("_id", None)
    return p


class TrackEvent(BaseModel):
    visitor_id: str
    session_id: Optional[str] = None
    event_type: str  # page_view | product_view | add_to_cart | checkout_start | order_confirmed | custom
    path: Optional[str] = None
    referrer: Optional[str] = None
    product_slug: Optional[str] = None
    device_type: Optional[str] = None  # mobile | tablet | desktop
    language: Optional[str] = None
    value_eur: Optional[float] = None
    extra: Optional[dict] = None
    analytics_consent: bool = False


@app.post("/api/analytics/track")
async def analytics_track(evt: TrackEvent, request: Request):
    doc = evt.model_dump()
    ref = doc.get("referrer") or ""
    try:
        host = urlparse(ref).hostname if ref else None
    except Exception:
        host = None
    doc["referrer_host"] = host
    doc = prepare_analytics_event(doc)
    if doc is None:
        return {"ok": True, "stored": False}
    doc["ts"] = datetime.now(timezone.utc).isoformat()
    await db.analytics_events.insert_one(doc)
    return {"ok": True, "stored": True}


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins() or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
