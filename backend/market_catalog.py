"""Market-observed catalog visibility, separate from offer/purchase readiness."""
from __future__ import annotations

from collections import defaultdict

from evidence import image_rights_evidence_verified


def _valid_gtin(value: object) -> bool:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) not in {8, 12, 13, 14}:
        return False
    total = sum(int(char) * (3 if index % 2 == 0 else 1) for index, char in enumerate(reversed(digits[:-1])))
    return (10 - total % 10) % 10 == int(digits[-1])


def dedupe_ads_products(rows: list[dict], catalog_products: list[dict]) -> list[dict]:
    by_gtin = {product.get("gtin_candidate_private"): product for product in catalog_products if product.get("gtin_candidate_private")}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        gtin = "".join(ch for ch in str(row.get("catalog_gtin") or "") if ch.isdigit())
        if gtin:
            grouped[gtin].append(row)
    result = []
    for gtin, ads in grouped.items():
        product = by_gtin.get(gtin)
        if not product:
            continue
        titles = []
        for ad in ads:
            title = (ad.get("product_title") or "").strip()
            if title and title not in titles:
                titles.append(title)
        result.append({
            "slug": product["slug"],
            "sku": product.get("sku"),
            "name": product.get("name"),
            "candidate_gtin": gtin,
            "checksum_valid": _valid_gtin(gtin),
            "creative_titles": titles,
            "creative_occurrences": sum(int(ad.get("creative_occurrences") or 0) for ad in ads),
            "ads_item_ids": sorted({item.strip() for ad in ads for item in (ad.get("ads_item_ids") or "").split("|") if item.strip()}),
        })
    return sorted(result, key=lambda item: item["slug"])


def catalog_display_failures(product: dict) -> list[str]:
    failures: list[str] = []
    if product.get("catalog_visibility_status") != "published_preview":
        failures.append("catalog_not_published")
    for field in ("name", "brand", "image_url"):
        if not product.get(field):
            failures.append(f"{field}_missing")
    if product.get("image_rights_approved") is not True or not image_rights_evidence_verified(
        product.get("image_rights_evidence_private")
    ):
        failures.append("image_rights_evidence_missing")
    return failures


def is_catalog_visible(product: dict) -> bool:
    return not catalog_display_failures(product)
