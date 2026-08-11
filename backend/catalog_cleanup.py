"""Deterministic, fail-closed cleanup helpers for imported catalog data."""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy

from publication import valid_gtin


def normalize_gtin(value: object) -> str | None:
    digits = "".join(ch for ch in str(value or "").strip() if ch.isdigit())
    return digits or None


def classify_gtins(rows: list[dict]) -> dict[str, str]:
    normalized = [normalize_gtin(row.get("gtin")) for row in rows]
    counts = Counter(value for value in normalized if value)
    result: dict[str, str] = {}
    for row, gtin in zip(rows, normalized):
        slug = row["product_slug"]
        if not gtin:
            result[slug] = "missing"
        elif not valid_gtin(gtin):
            result[slug] = "invalid_checksum"
        elif counts[gtin] > 1:
            result[slug] = "duplicate_conflict"
        else:
            result[slug] = "assignment_unverified"
    return result


def clean_catalog_rows(rows: list[dict]) -> tuple[list[dict], dict]:
    cleaned = deepcopy(rows)
    statuses = classify_gtins(cleaned)
    duplicate_gtins: dict[str, list[str]] = defaultdict(list)
    reference_skus: dict[str, list[str]] = defaultdict(list)

    for row in cleaned:
        slug = row["product_slug"]
        gtin = normalize_gtin(row.get("gtin"))
        row["gtin"] = gtin or ""
        row["gtin_status"] = statuses[slug]
        row["gtin_checksum_status"] = (
            "missing" if not gtin else "valid" if valid_gtin(gtin) else "invalid"
        )
        row["mpn_status"] = "assignment_unverified" if row.get("mpn") else "missing"
        row["merchant_approved"] = "False"
        row["selling_price"] = ""
        row["availability"] = "PendingReview"
        if gtin:
            duplicate_gtins[gtin].append(slug)
        if row.get("reference_sku_private"):
            reference_skus[row["reference_sku_private"]].append(slug)

    status_counts = Counter(row["gtin_status"] for row in cleaned)
    report = {
        "total_rows": len(cleaned),
        "unique_slugs": len({row["product_slug"] for row in cleaned}),
        "unique_product_ids": len({row["product_id"] for row in cleaned}),
        "unique_seller_skus": len({row["sku"] for row in cleaned}),
        "gtin_status_counts": dict(sorted(status_counts.items())),
        "duplicate_gtins": {
            value: slugs for value, slugs in sorted(duplicate_gtins.items()) if len(slugs) > 1
        },
        "duplicate_reference_skus": {
            value: slugs for value, slugs in sorted(reference_skus.items()) if len(slugs) > 1
        },
        "reference_price_missing": sum(not row.get("reference_price_private") for row in cleaned),
        "seller_prices_present": sum(bool(row.get("selling_price")) for row in cleaned),
        "approved_rows": sum(row.get("merchant_approved") == "True" for row in cleaned),
    }
    return cleaned, report
