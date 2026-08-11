"""Shared fail-closed publication rules for storefront, SEO and Merchant feed."""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable


def valid_gtin(value: str | None) -> bool:
    if not value:
        return False
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) not in {8, 12, 13, 14}:
        return False
    total = sum(
        int(char) * (3 if index % 2 == 0 else 1)
        for index, char in enumerate(reversed(digits[:-1]))
    )
    expected = (10 - total % 10) % 10
    return expected == int(digits[-1])


def offer_gate_failures(product: dict) -> list[str]:
    failures: list[str] = []
    if product.get("merchant_approved") is not True:
        failures.append("merchant_not_approved")
    if product.get("image_rights_approved") is not True:
        failures.append("image_rights_not_approved")
    if product.get("provenance_status") != "verified":
        failures.append("provenance_not_verified")
    if product.get("status") != "approved":
        failures.append("status_not_approved")
    if str(product.get("availability_status") or "").lower() not in {"instock", "in_stock"}:
        failures.append("not_in_stock")
    if int(product.get("stock") or 0) < 1:
        failures.append("no_stock")
    price = product.get("selling_price_eur")
    if not isinstance(price, (int, float)) or price <= 0:
        failures.append("missing_selling_price")
    if not product.get("sku"):
        failures.append("missing_sku")
    if not product.get("brand"):
        failures.append("missing_brand")
    if not product.get("image_url"):
        failures.append("missing_image")
    if product.get("condition") not in {"new", "used", "refurbished"}:
        failures.append("invalid_condition")

    gtin = product.get("gtin")
    if gtin:
        if product.get("gtin_status") != "valid" or not valid_gtin(gtin):
            failures.append("invalid_gtin")
    elif not product.get("mpn"):
        failures.append("missing_product_identifier")
    return failures


def is_public_offer(product: dict) -> bool:
    return not offer_gate_failures(product)


def to_public_product(product: dict) -> dict:
    public = deepcopy(product)
    ready = is_public_offer(product)
    if ready:
        variants = public.get("variants") or []
        if len(variants) == 1:
            variants[0]["price_eur"] = float(product["selling_price_eur"])
    public["merchant_ready"] = ready
    public["purchasable"] = ready
    if not ready:
        public["publication_blockers"] = offer_gate_failures(product)
    return public


def filter_storefront_products(products: Iterable[dict], app_env: str) -> list[dict]:
    if app_env == "production":
        return [to_public_product(product) for product in products if is_public_offer(product)]
    return [to_public_product(product) for product in products]
