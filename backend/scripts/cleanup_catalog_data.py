#!/usr/bin/env python3
"""Regenerate the normalized catalog CSV and its audit report."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from catalog_cleanup import clean_catalog_rows  # noqa: E402

CATALOG = BACKEND / "data" / "catalog.csv"
AUDIT = BACKEND / "data" / "catalog_audit.json"


def main() -> None:
    with CATALOG.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    cleaned, report = clean_catalog_rows(rows)

    original_fields = list(cleaned[0].keys())
    fields: list[str] = []
    for field in original_fields:
        fields.append(field)
        if field == "mpn":
            fields.append("mpn_status")
        if field == "gtin_status":
            fields.append("gtin_checksum_status")
    fields = list(dict.fromkeys(fields))

    with CATALOG.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(cleaned)

    report["generated_at"] = "2026-08-11"
    report["policy"] = {
        "gtin": "Checksum-valid values remain assignment_unverified until product-level evidence is approved; duplicates are blocked.",
        "mpn": "Imported MPN candidates remain assignment_unverified until manufacturer or supplier evidence is approved.",
        "prices": "Source prices remain reference_price_private; seller prices are empty and cannot be published implicitly.",
        "stock": "Source availability is ignored; stock remains zero until real licence inventory is imported.",
    }
    AUDIT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Rebuild the reproducible public-repository seed from the normalized loader.
    from catalog import _load_csv
    products = _load_csv()
    seed_path = BACKEND.parent / "database" / "seed" / "products.json"
    seed_path.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "rows": len(cleaned),
        "seed_products": len(products),
        "gtin_status_counts": report["gtin_status_counts"],
        "duplicate_gtins": len(report["duplicate_gtins"]),
    }))


if __name__ == "__main__":
    main()
