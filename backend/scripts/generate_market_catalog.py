#!/usr/bin/env python3
"""Build a 20-product public-preview shortlist from Ciaokey Ads Transparency evidence."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
WORKSPACE = ROOT.parent
sys.path.insert(0, str(BACKEND))

from catalog import _load_csv  # noqa: E402
from market_catalog import dedupe_ads_products  # noqa: E402

SOURCE = WORKSPACE / "ads_transparency_ciaokey" / "ciaokey_ads_transparency_prodotti_unici.csv"
OUTPUT = BACKEND / "data" / "ads_transparency_market_catalog.json"


def main() -> None:
    with SOURCE.open(encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    items = dedupe_ads_products(rows, _load_csv())
    if len(items) != 20:
        raise SystemExit(f"Expected 20 matched catalog products, found {len(items)}")
    if not all(item["checksum_valid"] for item in items):
        raise SystemExit("A market-observed candidate has an invalid checksum")
    for rank, item in enumerate(items, start=1):
        item.update({
            "rank": rank,
            "catalog_visibility_status": "published_preview",
            "identifier_status": "market_correlated_unverified",
            "declared_stock_private": 200,
            "stock_attestation_status_private": "user_attested_pending_key_import",
            "real_key_inventory_count": 0,
        })
    payload = {
        "version": 1,
        "source": {
            "name": "Google Ads Transparency Center",
            "url": "https://adstransparency.google.com/?region=IT&domain=ciaokey.it",
            "observed_at": "2026-08-11",
            "live_result": "~200 ads",
            "advertiser": "MACROKEY IT SRL",
            "advertiser_status": "verified",
            "extracted_creative_rows": len(rows),
            "distinct_catalog_products": len(items),
        },
        "policy": {
            "meaning": "Public catalog preview only",
            "merchant_feed_enabled": False,
            "purchasable": False,
            "stock_rule": "User-attested quantity is recorded privately; sellable stock remains zero until unique keys are imported.",
            "evidence_limit": "Competitor advertising corroborates market naming and identifier usage but does not prove LicenzPol provenance or authorization."
        },
        "items": items,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"creative_rows": len(rows), "distinct_products": len(items), "declared_each": 200, "real_keys": 0}))


if __name__ == "__main__":
    main()
