from publication import (
    filter_storefront_products,
    is_public_offer,
    offer_gate_failures,
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
        status="approved",
        availability_status="InStock",
        stock=3,
        selling_price_eur=19.90,
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


def test_production_storefront_contains_only_public_offers():
    approved = approved_product()
    assert filter_storefront_products([draft_product(), approved], "production") == [
        to_public_product(approved)
    ]


def test_staging_keeps_drafts_for_review_but_never_marks_them_purchasable():
    [preview] = filter_storefront_products([draft_product()], "staging")
    assert preview["merchant_ready"] is False
    assert preview["purchasable"] is False


def test_public_product_uses_selling_price_instead_of_reference_price():
    public = to_public_product(approved_product())
    assert public["variants"][0]["price_eur"] == 19.90
    assert public["purchasable"] is True


def test_invalid_gtin_blocks_offer_even_when_mpn_exists():
    product = approved_product()
    product.update(gtin="0760947037734", gtin_status="valid")
    assert "invalid_gtin" in offer_gate_failures(product)


def test_gtin_validator_uses_correct_gs1_check_digit_weighting():
    assert valid_gtin("0760947037735") is True
    assert valid_gtin("0760947037734") is False


def test_merchant_feed_uses_the_same_fail_closed_gate():
    assert _product_passes_gates(approved_product()) is True
    risky = approved_product()
    risky["provenance_status"] = "unverified"
    assert _product_passes_gates(risky) is False
