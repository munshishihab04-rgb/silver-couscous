from publication import (
    filter_storefront_products,
    is_public_offer,
    offer_gate_failures,
    public_price,
    to_public_product,
    valid_gtin,
)
from merchant_feed import _product_passes_gates


def draft_product():
    return {
        "slug": "office-test",
        "name": "Office Test",
        "brand": "Microsoft",
        "image_url": "/products/office-test.webp",
        "sku": "LP-TEST",
        "mpn": "TEST-MPN",
        "mpn_status": "assignment_unverified",
        "gtin": None,
        "gtin_status": None,
        "condition": "new",
        "merchant_approved": False,
        "image_rights_approved": False,
        "provenance_status": "unverified",
        "status": "draft",
        "availability_status": "PendingReview",
        "stock": 0,
        "selling_price_eur": None,
        "variants": [{"id": "office-test-v1", "price_eur": 9.99}],
    }


def approved_product():
    product = draft_product()
    product.update(
        merchant_approved=True,
        image_rights_approved=True,
        provenance_status="verified",
        catalog_review_status="approved",
        status="approved",
        availability_status="InStock",
        stock=3,
        selling_price_eur=19.90,
        mpn_status="verified",
        provenance_evidence_private={
            "supplier_name": "Verified Supplier S.r.l.",
            "source_type": "authorized_distributor",
            "evidence_refs": ["private://documents/supplier-agreement-2026"],
            "reviewed_by": "admin@licenzpol.it",
            "reviewed_at": "2026-08-11T00:00:00+00:00",
        },
        image_rights_evidence_private={
            "asset_path": "/products/office-test.webp",
            "sha256": "a" * 64,
            "width": 1000,
            "height": 1000,
            "rights_basis": "manufacturer_authorized",
            "evidence_refs": ["private://documents/image-authorization-2026"],
            "reviewed_by": "admin@licenzpol.it",
            "reviewed_at": "2026-08-11T00:00:00+00:00",
        },
    )
    return product


def test_draft_offer_fails_closed_with_explainable_reasons():
    reasons = offer_gate_failures(draft_product())
    assert "merchant_not_approved" in reasons
    assert "image_rights_not_approved" in reasons
    assert "provenance_not_verified" in reasons
    assert "no_stock" in reasons
    assert is_public_offer(draft_product()) is False


def test_complete_offer_is_public():
    assert offer_gate_failures(approved_product()) == []
    assert is_public_offer(approved_product()) is True


def test_inventory_cannot_publish_before_explicit_catalog_review():
    product = approved_product()
    product["catalog_review_status"] = "pending"
    assert "catalog_review_not_approved" in offer_gate_failures(product)


def test_flags_without_private_evidence_cannot_open_publication_gate():
    product = approved_product()
    product.pop("provenance_evidence_private")
    product.pop("image_rights_evidence_private")
    reasons = offer_gate_failures(product)
    assert "provenance_evidence_missing" in reasons
    assert "image_rights_evidence_missing" in reasons


def test_production_storefront_contains_only_public_offers():
    approved = approved_product()
    assert filter_storefront_products([draft_product(), approved], "production") == [
        to_public_product(approved)
    ]


def test_staging_keeps_drafts_for_review_but_never_marks_them_purchasable():
    [preview] = filter_storefront_products([draft_product()], "staging")
    assert preview["merchant_ready"] is False
    assert preview["purchasable"] is False


def test_public_price_is_missing_for_draft_and_authoritative_for_approved_offer():
    draft = draft_product()
    draft["selling_price_eur"] = 39.90
    draft["variants"][0]["price_eur"] = 39.90
    assert public_price(draft) is None
    public_draft = to_public_product(draft)
    assert public_draft["selling_price_eur"] is None
    assert public_draft["variants"][0]["price_eur"] is None
    assert public_price(approved_product()) == 19.90


def test_public_product_uses_selling_price_instead_of_reference_price():
    product = approved_product()
    product["gtin_candidate_private"] = "0760947037735"
    product["mpn_candidate_private"] = "PRIVATE-MPN"
    product["variants"][0]["reference_price_private"] = 9.99
    public = to_public_product(product)
    assert public["variants"][0]["price_eur"] == 19.90
    assert public["purchasable"] is True
    assert "gtin_candidate_private" not in public
    assert "mpn_candidate_private" not in public
    assert "reference_price_private" not in public["variants"][0]


def test_invalid_gtin_blocks_offer_even_when_mpn_exists():
    product = approved_product()
    product.update(gtin="0760947037734", gtin_status="verified")
    assert "invalid_gtin" in offer_gate_failures(product)


def test_checksum_valid_gtin_stays_blocked_until_assignment_is_verified():
    product = approved_product()
    product.update(gtin="0760947037735", gtin_status="assignment_unverified")
    reasons = offer_gate_failures(product)
    assert "gtin_assignment_unverified" in reasons
    product["gtin_status"] = "verified"
    assert offer_gate_failures(product) == []


def test_mpn_path_requires_assignment_verification():
    product = approved_product()
    product["mpn_status"] = "assignment_unverified"
    assert "mpn_assignment_unverified" in offer_gate_failures(product)


def test_gtin_validator_uses_correct_gs1_check_digit_weighting():
    assert valid_gtin("0760947037735") is True
    assert valid_gtin("0760947037734") is False


def test_merchant_feed_uses_the_same_fail_closed_gate():
    assert _product_passes_gates(approved_product()) is True
    risky = approved_product()
    risky["provenance_status"] = "unverified"
    assert _product_passes_gates(risky) is False
