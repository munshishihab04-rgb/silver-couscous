#!/usr/bin/env python3
"""Generate source-free LicenzPol artwork for the Ads Transparency shortlist."""
from __future__ import annotations

import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from pilot_images import render_product_image  # noqa: E402

MARKET = json.loads((BACKEND / "data" / "ads_transparency_market_catalog.json").read_text(encoding="utf-8"))
ASSETS = ROOT / "frontend" / "public" / "products"
PUBLIC_RECEIPT = BACKEND / "data" / "market_image_generation_receipt.json"
PRIVATE_RECEIPT = ROOT / ".runtime" / "evidence" / "documents" / "market-image-generation-2026-08-11.json"


def main() -> None:
    records = []
    for item in MARKET["items"]:
        output = ASSETS / f"{item['slug']}.webp"
        receipt = render_product_image(item["name"], item["name"].split()[0], output)
        records.append({"slug": item["slug"], "asset_path": f"/products/{item['slug']}.webp", **receipt})
    payload = {
        "version": 1,
        "generator": "backend/pilot_images.py",
        "method": "Deterministic Pillow rendering using only text, geometric primitives and DejaVu fonts.",
        "source_assets": [],
        "vendor_logos_used": False,
        "imported_package_art_used": False,
        "rights_basis": "owned",
        "items": records,
    }
    PUBLIC_RECEIPT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PRIVATE_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE_RECEIPT.write_text(json.dumps({**payload, "reviewed_by": "automation:hermes-agent"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"generated": len(records), "size": [1200, 1200], "source_assets": 0}))


if __name__ == "__main__":
    main()
