from pilot_catalog import catalog_review_blockers, shortlist_blockers, validate_review_row
from merchant_admin import catalog_review_update_blockers


def review_ready_product():
    return {
        "sku": "LP-PILOT",
        "brand": "Microsoft",
        "image_url": "/products/test.webp",
        "condition": "new",
        "selling_price_eur": 39.90,
        "google_product_category": "Software > Business & Productivity Software",
        "gtin": "0760947037735",
        "gtin_status": "verified",
        "mpn": None,
        "mpn_status": "missing",
        "provenance_status": "verified",
        "provenance_evidence_private": {
            "supplier_name": "Verified Supplier S.r.l.",
            "source_type": "authorized_distributor",
            "evidence_refs": ["private://documents/provenance-proof"],
            "reviewed_by": "admin@licenzpol.it",
            "reviewed_at": "2026-08-11T00:00:00+00:00",
        },
        "image_rights_approved": True,
        "image_rights_evidence_private": {
            "asset_path": "/products/test.webp",
            "sha256": "a" * 64,
            "width": 1000,
            "height": 1000,
            "rights_basis": "manufacturer_authorized",
            "evidence_refs": ["private://documents/image-proof"],
            "reviewed_by": "admin@licenzpol.it",
            "reviewed_at": "2026-08-11T00:00:00+00:00",
        },
    }


def test_shortlist_allows_unverified_assignment_but_rejects_bad_data():
    product = review_ready_product()
    product.update({"gtin_status": "assignment_unverified", "gtin_checksum_status": "valid"})
    assert shortlist_blockers(product) == []
    product["gtin_status"] = "duplicate_conflict"
    assert "identifier_conflict" in shortlist_blockers(product)


def test_catalog_review_requires_real_commercial_and_rights_evidence_but_not_stock():
    product = review_ready_product()
    assert catalog_review_blockers(product) == []
    product["selling_price_eur"] = None
    product["provenance_evidence_private"] = {}
    blockers = catalog_review_blockers(product)
    assert "selling_price_missing" in blockers
    assert "provenance_evidence_missing" in blockers
    assert "stock_missing" not in blockers


def test_admin_catalog_review_is_limited_to_shortlisted_ready_products():
    product = review_ready_product()
    assert catalog_review_update_blockers({**product, "pilot_candidate_private": False}, {"catalog_review_status": "approved"}) == ["pilot_not_selected"]
    assert catalog_review_update_blockers({**product, "pilot_candidate_private": True}, {"catalog_review_status": "approved"}) == []


def test_review_template_validation_requires_private_document_references_and_seller_price():
    row = {
        "selling_price_eur_vat_included": "39.90",
        "google_product_category": "Software > Business",
        "identifier_type": "gtin",
        "verified_identifier": "0760947037735",
        "identifier_evidence_ref": "private://documents/gtin-proof",
        "supplier_name": "Verified Supplier S.r.l.",
        "provenance_source_type": "authorized_distributor",
        "provenance_evidence_ref": "private://documents/provenance-proof",
        "image_rights_basis": "manufacturer_authorized",
        "image_evidence_ref": "private://documents/image-proof",
        "decision": "approved",
    }
    assert validate_review_row(row) == []
    row["selling_price_eur_vat_included"] = ""
    row["provenance_evidence_ref"] = "https://public.example/proof"
    assert validate_review_row(row) == ["selling_price_missing", "provenance_evidence_ref_invalid"]
