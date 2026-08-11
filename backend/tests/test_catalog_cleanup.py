from catalog_cleanup import classify_gtins, clean_catalog_rows, normalize_gtin

import csv
from pathlib import Path


def test_normalize_gtin_preserves_leading_zeroes_and_rejects_noise():
    assert normalize_gtin(" 0760947037735 ") == "0760947037735"
    assert normalize_gtin("not-a-code") is None


def test_gtin_classification_is_fail_closed():
    rows = [
        {"product_slug": "valid", "gtin": "0760947037735"},
        {"product_slug": "invalid", "gtin": "0760947037734"},
        {"product_slug": "missing", "gtin": ""},
        {"product_slug": "duplicate-a", "gtin": "4251755677283"},
        {"product_slug": "duplicate-b", "gtin": "4251755677283"},
    ]
    statuses = classify_gtins(rows)
    assert statuses == {
        "valid": "assignment_unverified",
        "invalid": "invalid_checksum",
        "missing": "missing",
        "duplicate-a": "duplicate_conflict",
        "duplicate-b": "duplicate_conflict",
    }


def test_real_catalog_cleanup_reconciles_all_rows_and_identifiers():
    path = Path(__file__).parents[1] / "data" / "catalog.csv"
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    cleaned, report = clean_catalog_rows(rows)
    assert len(cleaned) == 398
    assert report["unique_slugs"] == 398
    assert report["unique_seller_skus"] == 398
    assert report["gtin_status_counts"] == {
        "assignment_unverified": 374,
        "duplicate_conflict": 20,
        "invalid_checksum": 1,
        "missing": 3,
    }
    assert report["reference_price_missing"] == 1
    assert all(row["mpn_status"] == "assignment_unverified" for row in cleaned)
    assert all(row["merchant_approved"] == "False" for row in cleaned)
