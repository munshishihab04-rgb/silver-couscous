from db_migration import catalog_reconciliation_patch


def test_unapproved_product_is_reconciled_from_clean_seed():
    existing = {
        "slug": "product-a",
        "merchant_approved": False,
        "gtin": "old-public-gtin",
        "gtin_status": "valid",
        "variants": [{"id": "v1", "price_eur": 9.99}],
    }
    seed = {
        "slug": "product-a",
        "merchant_approved": False,
        "gtin": None,
        "gtin_status": "assignment_unverified",
        "gtin_candidate_private": "0760947037735",
        "variants": [{"id": "v1", "price_eur": None, "reference_price_private": 9.99}],
    }
    patch = catalog_reconciliation_patch(existing, seed)
    assert patch["gtin"] is None
    assert patch["gtin_status"] == "assignment_unverified"
    assert patch["variants"][0]["price_eur"] is None
    assert patch["variants"][0]["reference_price_private"] == 9.99


def test_human_approved_product_is_not_overwritten_by_catalog_cleanup():
    existing = {"slug": "product-a", "merchant_approved": True, "selling_price_eur": 29.90}
    seed = {"slug": "product-a", "merchant_approved": False, "selling_price_eur": None}
    assert catalog_reconciliation_patch(existing, seed) == {}


def test_in_progress_human_evidence_and_commercial_review_survive_restart():
    existing = {
        "slug": "product-a",
        "merchant_approved": False,
        "merchant_updated_at": "2026-08-11T00:00:00+00:00",
        "selling_price_eur": 29.90,
        "provenance_status": "verified",
        "provenance_evidence_private": {"evidence_refs": ["private://documents/proof"]},
    }
    seed = {
        "slug": "product-a",
        "merchant_approved": False,
        "selling_price_eur": None,
        "provenance_status": "unverified",
        "provenance_evidence_private": {},
        "name": "Clean catalog name",
    }
    patch = catalog_reconciliation_patch(existing, seed)
    assert patch["name"] == "Clean catalog name"
    assert patch["selling_price_eur"] == 29.90
    assert patch["provenance_status"] == "verified"
    assert patch["provenance_evidence_private"] == existing["provenance_evidence_private"]
