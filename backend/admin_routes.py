"""Admin panel API routes — all mounted under /api/admin.

Products, customers, tickets, pages (CMS), settings, users, analytics.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query
from pydantic import BaseModel, Field

from auth import (
    verify_password, hash_password, create_access_token,
    is_locked, bump_failed, clear_attempts, current_admin,
)

admin_router = APIRouter(prefix="/api/admin")


# ---------- helpers ---------------------------------------------------------

def _db(req: Request):
    return req.app.state.db


def _reload(req: Request):
    """Reload the in-memory PRODUCTS cache after any product mutation."""
    if hasattr(req.app.state, "reload_products"):
        return req.app.state.reload_products()


# ---------- Auth ------------------------------------------------------------

class LoginBody(BaseModel):
    email: str
    password: str


@admin_router.post("/auth/login")
async def admin_login(body: LoginBody, request: Request):
    db = _db(request)
    email = body.email.strip().lower()
    ip = request.client.host if request.client else "unknown"
    ident = f"{ip}:{email}"
    if await is_locked(db, ident):
        raise HTTPException(status_code=429, detail="Too many attempts, retry later.")
    user = await db.admin_users.find_one({"email": email})
    if not user or not verify_password(body.password, user.get("password_hash", "")):
        await bump_failed(db, ident)
        raise HTTPException(status_code=401, detail="Credenziali non valide.")
    await clear_attempts(db, ident)
    uid = str(user["_id"])
    token = create_access_token(uid, email, user.get("role", "admin"))
    return {
        "token": token,
        "user": {"id": uid, "email": email, "name": user.get("name", ""), "role": user.get("role", "admin")},
    }


@admin_router.get("/auth/me")
async def admin_me(user=Depends(current_admin)):
    return {"user": {"id": user["_id"], "email": user["email"], "name": user.get("name", ""), "role": user.get("role", "admin")}}


# ---------- Admin users management -------------------------------------------

class AdminUserCreate(BaseModel):
    email: str
    password: str
    name: str = ""


@admin_router.get("/users")
async def list_admins(request: Request, user=Depends(current_admin)):
    db = _db(request)
    out = []
    async for u in db.admin_users.find({}):
        out.append({
            "id": str(u["_id"]), "email": u["email"], "name": u.get("name", ""),
            "role": u.get("role", "admin"), "created_at": u.get("created_at"),
        })
    return out


@admin_router.post("/users")
async def create_admin(body: AdminUserCreate, request: Request, user=Depends(current_admin)):
    from datetime import datetime, timezone
    db = _db(request)
    email = body.email.strip().lower()
    if await db.admin_users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Email già registrata.")
    doc = {
        "email": email, "password_hash": hash_password(body.password),
        "name": body.name or "Admin", "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    res = await db.admin_users.insert_one(doc)
    return {"id": str(res.inserted_id), "email": email, "name": body.name}


@admin_router.delete("/users/{uid}")
async def delete_admin(uid: str, request: Request, user=Depends(current_admin)):
    from bson import ObjectId
    db = _db(request)
    if uid == user["_id"]:
        raise HTTPException(status_code=400, detail="Non puoi eliminare te stesso.")
    try:
        oid = ObjectId(uid)
    except Exception:
        raise HTTPException(status_code=400, detail="ID non valido.")
    await db.admin_users.delete_one({"_id": oid})
    return {"ok": True}


# ---------- Products -------------------------------------------------------

class Variant(BaseModel):
    id: str
    edition: str = "Standard"
    duration_months: int = 0
    devices: int = 1
    price_eur: float
    list_price_eur: Optional[float] = None


MERCHANT_CONTROLLED_FIELDS = {
    "merchant_approved", "image_rights_approved", "image_rights_evidence_private",
    "provenance_status", "provenance_evidence_private", "selling_price_eur",
    "stock", "sku", "gtin", "gtin_status", "mpn", "mpn_status",
    "availability_status", "condition", "google_product_category", "status",
}


def sanitize_product_editor_update(body: dict) -> dict:
    forbidden = MERCHANT_CONTROLLED_FIELDS.intersection(body)
    forbidden.update(key for key in body if key.endswith("_private"))
    if forbidden:
        raise ValueError("Campi Merchant riservati: " + ", ".join(sorted(forbidden)))
    return dict(body)


class ProductWrite(BaseModel):
    slug: str
    name: str
    category: str
    brand: str
    mark: str = ""
    colorKey: str = "work"
    image_url: Optional[str] = None
    platforms: List[str] = Field(default_factory=lambda: ["Windows"])
    licenseType: str = "Perpetua"
    tagline_it: str = ""
    tagline_en: str = ""
    description_it: str = ""
    description_en: str = ""
    features_it: List[str] = Field(default_factory=list)
    features_en: List[str] = Field(default_factory=list)
    variants: List[Variant] = Field(default_factory=list)
    compatibility_it: str = ""
    compatibility_en: str = ""
    whatYouGet_it: List[str] = Field(default_factory=list)
    whatYouGet_en: List[str] = Field(default_factory=list)
    activation_it: List[str] = Field(default_factory=list)
    activation_en: List[str] = Field(default_factory=list)
    faq: List[dict] = Field(default_factory=list)


@admin_router.get("/products")
async def admin_products(
    request: Request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    limit: int = 500,
    skip: int = 0,
    user=Depends(current_admin),
):
    db = _db(request)
    query = {}
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"brand": {"$regex": q, "$options": "i"}},
            {"slug": {"$regex": q, "$options": "i"}},
        ]
    if category:
        query["category"] = category
    if brand:
        query["brand"] = brand
    total = await db.products.count_documents(query)
    items = []
    async for p in db.products.find(query).sort("name", 1).skip(skip).limit(limit):
        p.pop("_id", None)
        items.append(p)
    return {"total": total, "items": items}


@admin_router.get("/products/{slug}")
async def admin_get_product(slug: str, request: Request, user=Depends(current_admin)):
    db = _db(request)
    p = await db.products.find_one({"slug": slug})
    if not p:
        raise HTTPException(status_code=404, detail="Non trovato.")
    p.pop("_id", None)
    return p


@admin_router.post("/products")
async def admin_create_product(body: ProductWrite, request: Request, user=Depends(current_admin)):
    db = _db(request)
    existing = await db.products.find_one({"slug": body.slug})
    if existing:
        raise HTTPException(status_code=409, detail="Slug già esistente.")
    doc = body.model_dump()
    doc["_id"] = doc["slug"]
    doc["id"] = doc["slug"]
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.products.insert_one(doc)
    await _reload(request)
    doc.pop("_id", None)
    return doc


@admin_router.patch("/products/{slug}")
async def admin_update_product(slug: str, body: dict = Body(...), request: Request = None, user=Depends(current_admin)):
    db = _db(request)
    body.pop("_id", None)
    body.pop("slug", None)  # slug is immutable
    try:
        body = sanitize_product_editor_update(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = await db.products.update_one({"slug": slug}, {"$set": body})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Non trovato.")
    await _reload(request)
    doc = await db.products.find_one({"slug": slug})
    doc.pop("_id", None)
    return doc


@admin_router.delete("/products/{slug}")
async def admin_delete_product(slug: str, request: Request, user=Depends(current_admin)):
    db = _db(request)
    res = await db.products.delete_one({"slug": slug})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Non trovato.")
    await _reload(request)
    return {"ok": True}


# ---------- Customers (derived from orders) ---------------------------------

@admin_router.get("/customers")
async def admin_customers(request: Request, q: Optional[str] = None, user=Depends(current_admin)):
    db = _db(request)
    match_stage = {}
    if q:
        match_stage["$or"] = [
            {"email": {"$regex": q, "$options": "i"}},
            {"first_name": {"$regex": q, "$options": "i"}},
            {"last_name": {"$regex": q, "$options": "i"}},
        ]
    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})
    pipeline += [
        {"$group": {
            "_id": "$email",
            "email": {"$first": "$email"},
            "first_name": {"$last": "$first_name"},
            "last_name": {"$last": "$last_name"},
            "country": {"$last": "$country"},
            "company": {"$last": "$company"},
            "orders": {"$sum": 1},
            "revenue": {"$sum": "$total_eur"},
            "last_order_at": {"$max": "$created_at"},
        }},
        {"$sort": {"last_order_at": -1}},
        {"$limit": 500},
    ]
    out = []
    async for r in db.orders.aggregate(pipeline):
        r.pop("_id", None)
        out.append(r)
    return out


@admin_router.get("/customers/{email}")
async def admin_customer_detail(email: str, request: Request, user=Depends(current_admin)):
    db = _db(request)
    email = email.lower()
    orders = []
    async for o in db.orders.find({"email": email}).sort("created_at", -1):
        o.pop("_id", None)
        orders.append(o)
    if not orders:
        raise HTTPException(status_code=404, detail="Cliente non trovato.")
    return {
        "email": email,
        "first_name": orders[0].get("first_name"),
        "last_name": orders[0].get("last_name"),
        "country": orders[0].get("country"),
        "company": orders[0].get("company"),
        "vat": orders[0].get("vat"),
        "orders": orders,
        "total_revenue": sum(o.get("total_eur", 0) for o in orders),
    }


# ---------- Orders ----------------------------------------------------------

ALLOWED_ORDER_STATUSES = {
    "pending", "demo_confirmed", "paid", "delivered", "cancelled", "refunded",
}


class OrderStatusUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None


@admin_router.get("/orders")
async def admin_orders(
    request: Request,
    limit: int = 200,
    skip: int = 0,
    q: Optional[str] = None,
    status: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    user=Depends(current_admin),
):
    db = _db(request)
    query = {}
    if q:
        query["$or"] = [
            {"email": {"$regex": q, "$options": "i"}},
            {"reference": {"$regex": q, "$options": "i"}},
            {"first_name": {"$regex": q, "$options": "i"}},
            {"last_name": {"$regex": q, "$options": "i"}},
        ]
    if status:
        query["status"] = status
    if start:
        query.setdefault("created_at", {})["$gte"] = start
    if end:
        query.setdefault("created_at", {})["$lte"] = end

    total = await db.orders.count_documents(query)
    items = []
    async for o in db.orders.find(query).sort("created_at", -1).skip(skip).limit(limit):
        o.pop("_id", None)
        items.append(o)
    return {"total": total, "items": items}


@admin_router.get("/orders/{reference}")
async def admin_get_order(reference: str, request: Request, user=Depends(current_admin)):
    db = _db(request)
    o = await db.orders.find_one({"reference": reference})
    if not o:
        raise HTTPException(status_code=404, detail="Ordine non trovato.")
    o.pop("_id", None)
    return o


@admin_router.patch("/orders/{reference}")
async def admin_update_order(
    reference: str, body: OrderStatusUpdate,
    request: Request, user=Depends(current_admin),
):
    db = _db(request)
    if body.status not in ALLOWED_ORDER_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status non valido. Consentiti: {sorted(ALLOWED_ORDER_STATUSES)}")
    update = {"status": body.status,
              "updated_at": datetime.now(timezone.utc).isoformat()}
    if body.admin_notes is not None:
        update["admin_notes"] = body.admin_notes
    res = await db.orders.update_one({"reference": reference}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ordine non trovato.")
    o = await db.orders.find_one({"reference": reference})
    o.pop("_id", None)
    return o


@admin_router.delete("/orders/{reference}")
async def admin_delete_order(reference: str, request: Request, user=Depends(current_admin)):
    db = _db(request)
    res = await db.orders.delete_one({"reference": reference})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ordine non trovato.")
    return {"ok": True}


# ---------- Tickets (support messages) --------------------------------------

class TicketUpdate(BaseModel):
    status: Optional[str] = None      # open / in_progress / closed
    admin_notes: Optional[str] = None


@admin_router.get("/tickets")
async def admin_tickets(request: Request, status: Optional[str] = None, user=Depends(current_admin)):
    db = _db(request)
    q = {}
    if status:
        q["status"] = status
    out = []
    async for t in db.support_messages.find(q).sort("created_at", -1):
        t["id"] = t.get("id") or str(t.get("_id"))
        t.pop("_id", None)
        t.setdefault("status", "open")
        out.append(t)
    return out


@admin_router.patch("/tickets/{tid}")
async def admin_update_ticket(tid: str, body: TicketUpdate, request: Request, user=Depends(current_admin)):
    db = _db(request)
    update = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="Nessun campo da aggiornare.")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = await db.support_messages.update_one({"id": tid}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket non trovato.")
    return {"ok": True}


# ---------- CMS Pages -------------------------------------------------------

class PageWrite(BaseModel):
    title_it: str
    title_en: str
    content_it: str
    content_en: str


@admin_router.get("/pages")
async def admin_list_pages(request: Request, user=Depends(current_admin)):
    db = _db(request)
    out = []
    async for p in db.pages.find({}):
        p.pop("_id", None)
        out.append(p)
    return out


@admin_router.get("/pages/{slug}")
async def admin_get_page(slug: str, request: Request, user=Depends(current_admin)):
    db = _db(request)
    p = await db.pages.find_one({"slug": slug})
    if not p:
        raise HTTPException(status_code=404, detail="Pagina non trovata.")
    p.pop("_id", None)
    return p


@admin_router.put("/pages/{slug}")
async def admin_upsert_page(slug: str, body: PageWrite, request: Request, user=Depends(current_admin)):
    db = _db(request)
    doc = body.model_dump()
    doc["slug"] = slug
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.pages.update_one({"slug": slug}, {"$set": doc}, upsert=True)
    return doc


# ---------- Settings --------------------------------------------------------

@admin_router.get("/settings")
async def admin_get_settings(request: Request, user=Depends(current_admin)):
    db = _db(request)
    s = await db.settings.find_one({"key": "site"}) or {}
    s.pop("_id", None)
    return s


@admin_router.patch("/settings")
async def admin_update_settings(body: dict = Body(...), request: Request = None, user=Depends(current_admin)):
    db = _db(request)
    body.pop("_id", None)
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.settings.update_one({"key": "site"}, {"$set": body}, upsert=True)
    s = await db.settings.find_one({"key": "site"})
    s.pop("_id", None)
    return s


# ---------- Analytics -------------------------------------------------------

def _parse_range(range_key: str) -> int:
    return {"24h": 1, "7d": 7, "30d": 30, "90d": 90}.get(range_key, 7)


@admin_router.get("/analytics/overview")
async def admin_analytics_overview(request: Request, range: str = "7d", user=Depends(current_admin)):
    db = _db(request)
    days = _parse_range(range)
    since_dt = datetime.now(timezone.utc) - timedelta(days=days)
    since = since_dt.isoformat()

    events_match = {"ts": {"$gte": since}}
    total_events = await db.analytics_events.count_documents(events_match)
    page_views = await db.analytics_events.count_documents({**events_match, "event_type": "page_view"})
    unique_visitors = len(await db.analytics_events.distinct("visitor_id", events_match))
    add_to_cart = await db.analytics_events.count_documents({**events_match, "event_type": "add_to_cart"})
    checkouts = await db.analytics_events.count_documents({**events_match, "event_type": "checkout_start"})

    orders_pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {"$group": {"_id": None, "count": {"$sum": 1}, "revenue": {"$sum": "$total_eur"}}},
    ]
    orders_stats = {"count": 0, "revenue": 0}
    async for r in db.orders.aggregate(orders_pipeline):
        orders_stats = {"count": r["count"], "revenue": round(r.get("revenue", 0), 2)}

    # Top pages
    top_pages_pipeline = [
        {"$match": {**events_match, "event_type": "page_view"}},
        {"$group": {"_id": "$path", "views": {"$sum": 1}}},
        {"$sort": {"views": -1}},
        {"$limit": 10},
    ]
    top_pages = []
    async for r in db.analytics_events.aggregate(top_pages_pipeline):
        top_pages.append({"path": r["_id"] or "(unknown)", "views": r["views"]})

    # Top products (from product_view events)
    top_products_pipeline = [
        {"$match": {**events_match, "event_type": "product_view", "product_slug": {"$ne": None}}},
        {"$group": {"_id": "$product_slug", "views": {"$sum": 1}}},
        {"$sort": {"views": -1}},
        {"$limit": 10},
    ]
    top_products = []
    async for r in db.analytics_events.aggregate(top_products_pipeline):
        top_products.append({"slug": r["_id"], "views": r["views"]})

    # Timeseries by day
    ts_pipeline = [
        {"$match": events_match},
        {"$group": {
            "_id": {"$substr": ["$ts", 0, 10]},
            "events": {"$sum": 1},
            "page_views": {"$sum": {"$cond": [{"$eq": ["$event_type", "page_view"]}, 1, 0]}},
            "visitors_set": {"$addToSet": "$visitor_id"},
        }},
        {"$project": {"date": "$_id", "_id": 0, "events": 1, "page_views": 1, "visitors": {"$size": "$visitors_set"}}},
        {"$sort": {"date": 1}},
    ]
    timeseries = []
    async for r in db.analytics_events.aggregate(ts_pipeline):
        timeseries.append(r)

    # Referrers
    ref_pipeline = [
        {"$match": {**events_match, "event_type": "page_view", "referrer_host": {"$nin": [None, ""]}}},
        {"$group": {"_id": "$referrer_host", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 8},
    ]
    referrers = []
    async for r in db.analytics_events.aggregate(ref_pipeline):
        referrers.append({"host": r["_id"], "count": r["count"]})

    # Devices
    dev_pipeline = [
        {"$match": events_match},
        {"$group": {"_id": "$device_type", "count": {"$sum": 1}}},
    ]
    devices = {"mobile": 0, "tablet": 0, "desktop": 0}
    async for r in db.analytics_events.aggregate(dev_pipeline):
        k = r["_id"] or "desktop"
        devices[k] = devices.get(k, 0) + r["count"]

    return {
        "range": range,
        "since": since,
        "kpis": {
            "unique_visitors": unique_visitors,
            "page_views": page_views,
            "events": total_events,
            "add_to_cart": add_to_cart,
            "checkouts": checkouts,
            "orders": orders_stats["count"],
            "revenue_eur": orders_stats["revenue"],
        },
        "top_pages": top_pages,
        "top_products": top_products,
        "timeseries": timeseries,
        "referrers": referrers,
        "devices": devices,
    }


@admin_router.get("/analytics/live")
async def admin_analytics_live(request: Request, user=Depends(current_admin)):
    db = _db(request)
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    active = len(await db.analytics_events.distinct("visitor_id", {"ts": {"$gte": cutoff}}))
    recent = []
    async for e in db.analytics_events.find({"ts": {"$gte": cutoff}}).sort("ts", -1).limit(20):
        e.pop("_id", None)
        recent.append(e)
    return {"active_visitors": active, "recent_events": recent}
