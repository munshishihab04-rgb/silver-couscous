"""Google Merchant Center compatible product feed (XML).

Fail-closed: only merchant_approved products with stock > 0 and required fields
are included. If none pass, the feed is intentionally empty.

Structure follows the Google product feed specification.
"""

from datetime import datetime, timezone
from typing import Optional
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, Request, Response

from config import PUBLIC_SITE_URL, is_production
from publication import is_public_offer

merchant_router = APIRouter()


def _site_base(request: Request) -> str:
    if PUBLIC_SITE_URL:
        return PUBLIC_SITE_URL
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    return f"{proto}://{host}".rstrip("/") if host else str(request.base_url).rstrip("/")


def _product_passes_gates(p: dict) -> bool:
    return is_public_offer(p)


@merchant_router.get("/api/merchant/feed.xml", include_in_schema=False)
async def merchant_feed_xml(request: Request):
    base = _site_base(request)
    db = request.app.state.db

    items_xml = []
    query = {"merchant_approved": True} if is_production() else {"_id": {"$exists": False}}
    async for p in db.products.find(query):
        if not _product_passes_gates(p):
            continue
        sku = p["sku"]
        title = p.get("name", "")
        description = (p.get("description_it") or p.get("tagline_it") or title)[:5000]
        link = f"{base}/product/{p['slug']}"
        image = p.get("image_url") or ""
        if image and image.startswith("/"):
            image = base + image
        brand = p.get("brand", "")
        condition = p.get("condition", "new")
        availability = "in_stock" if (p.get("stock") or 0) > 0 else "out_of_stock"
        price = f"{float(p['selling_price_eur']):.2f} EUR"
        gtin = p.get("gtin") or ""
        mpn = p.get("mpn") or ""
        identifier_exists = "yes" if (gtin or mpn) else "no"
        item_group_id = p.get("item_group_id") or sku.split("-", 1)[0]

        item = ["    <item>"]
        item.append(f"      <g:id>{xml_escape(sku)}</g:id>")
        item.append(f"      <title>{xml_escape(title)}</title>")
        item.append(f"      <description>{xml_escape(description)}</description>")
        item.append(f"      <link>{xml_escape(link)}</link>")
        if image:
            item.append(f"      <g:image_link>{xml_escape(image)}</g:image_link>")
        item.append(f"      <g:availability>{availability}</g:availability>")
        item.append(f"      <g:price>{price}</g:price>")
        if brand:
            item.append(f"      <g:brand>{xml_escape(brand)}</g:brand>")
        item.append(f"      <g:condition>{xml_escape(condition)}</g:condition>")
        item.append(f"      <g:identifier_exists>{identifier_exists}</g:identifier_exists>")
        if gtin:
            item.append(f"      <g:gtin>{xml_escape(gtin)}</g:gtin>")
        if mpn:
            item.append(f"      <g:mpn>{xml_escape(mpn)}</g:mpn>")
        item.append(f"      <g:item_group_id>{xml_escape(item_group_id)}</g:item_group_id>")
        if p.get("google_product_category"):
            item.append(f"      <g:google_product_category>{xml_escape(p['google_product_category'])}</g:google_product_category>")
        item.append("    </item>")
        items_xml.append("\n".join(item))

    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">
  <channel>
    <title>LicenzPøl · Product feed</title>
    <link>{xml_escape(base)}</link>
    <description>Software licenses catalog · merchant-approved offers only</description>
    <lastBuildDate>{updated_at}</lastBuildDate>
{chr(10).join(items_xml)}
  </channel>
</rss>
'''
    return Response(
        content=xml,
        media_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=900"},
    )


@merchant_router.get("/api/merchant/health", include_in_schema=False)
async def merchant_health(request: Request):
    db = request.app.state.db
    approved = await db.products.count_documents({"merchant_approved": True})
    feedable = 0
    if is_production():
        async for p in db.products.find({"merchant_approved": True}):
            if is_public_offer(p):
                feedable += 1
    return {
        "approved": approved,
        "feedable": feedable,
        "production_mode": is_production(),
    }
