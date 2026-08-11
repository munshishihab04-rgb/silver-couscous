"""CSV exports for admin (orders, customers, products, analytics events)
and public SEO endpoints (sitemap.xml, robots.txt).
"""

from datetime import datetime, timezone
from io import StringIO
import csv
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, Depends, Request, Response, Query, HTTPException

from auth import current_admin


exports_router = APIRouter(prefix="/api/admin/exports")
seo_router = APIRouter()


def _db(req: Request):
    return req.app.state.db


def _csv_response(rows, headers, filename: str) -> Response:
    """Turn a list of dict rows into a CSV file response."""
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        # Flatten any lists/dicts to string for safety
        row = {}
        for h in headers:
            v = r.get(h)
            if isinstance(v, (list, dict)):
                row[h] = str(v)
            elif v is None:
                row[h] = ""
            else:
                row[h] = v
        writer.writerow(row)
    csv_data = buf.getvalue()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}-{ts}.csv"',
            "Cache-Control": "no-store",
        },
    )


# ---------- Order status management ----------------------------------------

ALLOWED_STATUSES = {"pending", "demo_confirmed", "paid", "delivered", "cancelled", "refunded"}


@exports_router.get("/orders.csv")
async def export_orders_csv(
    request: Request,
    start: Optional[str] = None,
    end: Optional[str] = None,
    status: Optional[str] = None,
    user=Depends(current_admin),
):
    db = _db(request)
    query = {}
    if start:
        query.setdefault("created_at", {})["$gte"] = start
    if end:
        query.setdefault("created_at", {})["$lte"] = end
    if status:
        query["status"] = status

    rows = []
    async for o in db.orders.find(query).sort("created_at", -1):
        o.pop("_id", None)
        items = o.get("items", [])
        rows.append({
            "reference": o.get("reference"),
            "created_at": o.get("created_at"),
            "status": o.get("status"),
            "email": o.get("email"),
            "first_name": o.get("first_name"),
            "last_name": o.get("last_name"),
            "country": o.get("country"),
            "company": o.get("company"),
            "vat": o.get("vat"),
            "language": o.get("language"),
            "items_count": len(items),
            "items_names": " | ".join(i.get("product_name", "") for i in items),
            "subtotal_eur": o.get("subtotal_eur"),
            "total_eur": o.get("total_eur"),
        })

    headers = [
        "reference", "created_at", "status", "email", "first_name", "last_name",
        "country", "company", "vat", "language",
        "items_count", "items_names", "subtotal_eur", "total_eur",
    ]
    return _csv_response(rows, headers, "orders")


@exports_router.get("/customers.csv")
async def export_customers_csv(request: Request, user=Depends(current_admin)):
    db = _db(request)
    pipeline = [
        {"$group": {
            "_id": "$email",
            "email": {"$first": "$email"},
            "first_name": {"$last": "$first_name"},
            "last_name": {"$last": "$last_name"},
            "country": {"$last": "$country"},
            "company": {"$last": "$company"},
            "vat": {"$last": "$vat"},
            "orders": {"$sum": 1},
            "revenue": {"$sum": "$total_eur"},
            "first_order_at": {"$min": "$created_at"},
            "last_order_at": {"$max": "$created_at"},
        }},
        {"$sort": {"last_order_at": -1}},
    ]
    rows = []
    async for r in db.orders.aggregate(pipeline):
        r.pop("_id", None)
        r["revenue"] = round(r.get("revenue", 0) or 0, 2)
        rows.append(r)
    headers = [
        "email", "first_name", "last_name", "country", "company", "vat",
        "orders", "revenue", "first_order_at", "last_order_at",
    ]
    return _csv_response(rows, headers, "customers")


@exports_router.get("/products.csv")
async def export_products_csv(request: Request, user=Depends(current_admin)):
    db = _db(request)
    rows = []
    async for p in db.products.find({}).sort("name", 1):
        p.pop("_id", None)
        variants = p.get("variants", []) or []
        prices = [v.get("price_eur", 0) for v in variants]
        rows.append({
            "slug": p.get("slug"),
            "name": p.get("name"),
            "brand": p.get("brand"),
            "category": p.get("category"),
            "licenseType": p.get("licenseType"),
            "platforms": ",".join(p.get("platforms", []) or []),
            "variants_count": len(variants),
            "price_from_eur": min(prices) if prices else "",
            "price_to_eur": max(prices) if prices else "",
            "updated_at": p.get("updated_at", ""),
        })
    headers = [
        "slug", "name", "brand", "category", "licenseType", "platforms",
        "variants_count", "price_from_eur", "price_to_eur", "updated_at",
    ]
    return _csv_response(rows, headers, "products")


@exports_router.get("/analytics.csv")
async def export_analytics_csv(
    request: Request,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = Query(10000, le=100000),
    user=Depends(current_admin),
):
    db = _db(request)
    q = {}
    if start:
        q.setdefault("ts", {})["$gte"] = start
    if end:
        q.setdefault("ts", {})["$lte"] = end
    rows = []
    async for e in db.analytics_events.find(q).sort("ts", -1).limit(limit):
        e.pop("_id", None)
        rows.append({
            "ts": e.get("ts"),
            "event_type": e.get("event_type"),
            "visitor_id": e.get("visitor_id"),
            "session_id": e.get("session_id"),
            "path": e.get("path"),
            "product_slug": e.get("product_slug"),
            "device_type": e.get("device_type"),
            "language": e.get("language"),
            "referrer_host": e.get("referrer_host"),
            "value_eur": e.get("value_eur"),
            "ip": e.get("ip"),
        })
    headers = [
        "ts", "event_type", "visitor_id", "session_id", "path", "product_slug",
        "device_type", "language", "referrer_host", "value_eur", "ip",
    ]
    return _csv_response(rows, headers, "analytics")


# ---------- SEO: sitemap.xml & robots.txt -----------------------------------

def _site_base_url(request: Request) -> str:
    # Prefer the Origin/Referer/X-Forwarded headers; fall back to request URL
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if forwarded_host:
        proto = forwarded_proto or ("https" if request.url.scheme == "https" else "http")
        return f"{proto}://{forwarded_host}".rstrip("/")
    return str(request.base_url).rstrip("/")


@seo_router.get("/api/sitemap.xml", include_in_schema=False)
@seo_router.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml(request: Request):
    """Dynamic sitemap covering static pages, families, and all products."""
    base = _site_base_url(request)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db = request.app.state.db

    urls = []

    def add(loc: str, changefreq: str = "weekly", priority: str = "0.6", lastmod: str = None):
        urls.append({
            "loc": xml_escape(f"{base}{loc}"),
            "lastmod": lastmod or now,
            "changefreq": changefreq,
            "priority": priority,
        })

    # Static pages
    add("/", "daily", "1.0")
    add("/catalog", "daily", "0.9")
    add("/needs", "weekly", "0.7")
    add("/families", "weekly", "0.8")
    add("/bundle", "monthly", "0.6")
    add("/compare", "monthly", "0.4")
    add("/support", "monthly", "0.5")
    add("/transparency", "monthly", "0.4")
    add("/legal/privacy", "monthly", "0.3")
    add("/legal/terms", "monthly", "0.3")
    add("/legal/cookies", "monthly", "0.3")

    # Families
    try:
        from families import FAMILIES
        for f in FAMILIES:
            add(f"/family/{f.get('slug')}", "weekly", "0.7")
    except Exception:
        pass

    # Products from DB
    async for p in db.products.find({}, {"slug": 1, "updated_at": 1}):
        slug = p.get("slug")
        if not slug:
            continue
        lastmod = p.get("updated_at") or now
        # normalize ISO timestamp -> YYYY-MM-DD
        if isinstance(lastmod, str) and len(lastmod) >= 10:
            lastmod = lastmod[:10]
        add(f"/product/{slug}", "weekly", "0.6", lastmod)

    # CMS pages (public)
    async for pg in db.pages.find({}, {"slug": 1, "updated_at": 1}):
        slug = pg.get("slug")
        if not slug or slug in ("privacy", "terms", "cookies", "transparency"):
            continue
        add(f"/page/{slug}", "monthly", "0.4")

    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml_parts.append("  <url>")
        xml_parts.append(f"    <loc>{u['loc']}</loc>")
        xml_parts.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        xml_parts.append(f"    <changefreq>{u['changefreq']}</changefreq>")
        xml_parts.append(f"    <priority>{u['priority']}</priority>")
        xml_parts.append("  </url>")
    xml_parts.append("</urlset>")

    return Response(
        content="\n".join(xml_parts),
        media_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@seo_router.get("/api/robots.txt", include_in_schema=False)
async def robots_txt(request: Request):
    base = _site_base_url(request)
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        "Disallow: /api/\n"
        "Disallow: /checkout\n"
        "\n"
        f"Sitemap: {base}/api/sitemap.xml\n"
    )
    return Response(content=body, media_type="text/plain; charset=utf-8")
