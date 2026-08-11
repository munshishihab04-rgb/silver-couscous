#!/usr/bin/env python3
"""Generate the Phase 5 pilot shortlist and human-review import template."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from catalog import PRODUCTS  # noqa: E402
from pilot_catalog import catalog_review_blockers, shortlist_blockers  # noqa: E402

PILOT_SLUGS = [
    "microsoft-office-2024-home-and-business-mac",
    "microsoft-office-2024-home-and-business-windows",
    "microsoft-windows-11-professional",
    "microsoft-windows-11-home",
    "bitdefender-antivirus-plus-1-pc-1-anno",
    "bitdefender-antivirus-plus-3-pc-1-anno",
    "bitdefender-antivirus-plus-5-pc-1-anno",
    "bitdefender-total-security-licenza-3-dispositivi-1-anno",
    "bitdefender-total-security-licenza-5-dispositivi-1-anno",
    "bitdefender-total-security-licenza-10-dispositivi-1-anno",
]

DATA = BACKEND / "data"
MANIFEST = DATA / "pilot_catalog.json"
TEMPLATE = DATA / "pilot_review_template.csv"


def main() -> None:
    by_slug = {product["slug"]: product for product in PRODUCTS}
    taxonomy = json.loads((DATA / "google_taxonomy_pilot.json").read_text(encoding="utf-8"))
    google_mapping = taxonomy.get("mapping", {})
    pricing = json.loads((DATA / "pilot_pricing.json").read_text(encoding="utf-8"))
    pilot_prices = pricing.get("prices", {})
    missing = [slug for slug in PILOT_SLUGS if slug not in by_slug]
    if missing:
        raise SystemExit(f"Missing pilot products: {missing}")

    items = []
    template_rows = []
    for rank, slug in enumerate(PILOT_SLUGS, start=1):
        product = by_slug[slug]
        shortlist_failures = shortlist_blockers(product)
        if shortlist_failures:
            raise SystemExit(f"Unsafe pilot candidate {slug}: {shortlist_failures}")
        review_failures = catalog_review_blockers(product)
        items.append({
            "rank": rank,
            "slug": slug,
            "sku": product["sku"],
            "name": product["name"],
            "brand": product["brand"],
            "category": product["category"],
            "shortlist_status": "candidate",
            "catalog_review_status": "pending",
            "review_blockers": review_failures,
        })
        template_rows.append({
            "slug": slug,
            "sku": product["sku"],
            "name": product["name"],
            "selling_price_eur_vat_included": pilot_prices.get(slug, ""),
            "google_product_category": google_mapping.get(slug, ""),
            "identifier_type": "",
            "verified_identifier": "",
            "identifier_evidence_ref": "",
            "supplier_name": "",
            "provenance_source_type": "",
            "provenance_evidence_ref": "",
            "image_rights_basis": "owned",
            "image_evidence_ref": "private://documents/pilot-image-generation-2026-08-11",
            "decision": "pending",
            "review_notes": "",
        })

    payload = {
        "version": 1,
        "phase": 5,
        "status": "prepared_not_approved",
        "selection_policy": {
            "count": len(items),
            "formal_gtin_checksum_required": True,
            "duplicate_or_invalid_identifiers_excluded": True,
            "minimum_image_side_px": 500,
            "commercial_approval_inferred": False,
            "source_price_used_as_selling_price": False,
        },
        "items": items,
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with TEMPLATE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(template_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(template_rows)
    print(json.dumps({
        "pilot_candidates": len(items),
        "approved": 0,
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "template": str(TEMPLATE.relative_to(ROOT)),
    }))


if __name__ == "__main__":
    main()
