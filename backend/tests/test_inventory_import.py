from inventory_import import analyse_rows


def test_inventory_csv_analysis_rejects_unknown_blank_and_duplicate_without_echoing_keys():
    rows = [
        {"sku": "LP-A", "key": " SECRET-1 ", "source": "supplier"},
        {"sku": "LP-A", "key": "SECRET-1", "source": "supplier"},
        {"sku": "UNKNOWN", "key": "SECRET-2", "source": "supplier"},
        {"sku": "LP-A", "key": "", "source": "supplier"},
        {"sku": "LP-B", "key": "SECRET-3", "source": "supplier"},
    ]
    valid, report = analyse_rows(rows, {"LP-A", "LP-B"})
    assert valid == [
        {"sku": "LP-A", "key": "SECRET-1", "source": "supplier"},
        {"sku": "LP-B", "key": "SECRET-3", "source": "supplier"},
    ]
    assert report == {
        "rows": 5,
        "valid": 2,
        "duplicates_in_file": 1,
        "blank_or_invalid": 1,
        "unknown_sku": 1,
        "per_sku": {"LP-A": 1, "LP-B": 1},
    }
    assert "SECRET" not in str(report)
