from merchant_admin import approval_blockers


def test_admin_cannot_approve_product_with_unverified_identifier():
    product = {
        "merchant_approved": False,
        "image_rights_approved": True,
        "provenance_status": "verified",
        "status": "draft",
        "availability_status": "InStock",
        "stock": 1,
        "selling_price_eur": 19.9,
        "sku": "LP-TEST",
        "brand": "Microsoft",
        "image_url": "/products/test.webp",
        "condition": "new",
        "gtin": "0760947037735",
        "gtin_status": "assignment_unverified",
        "mpn": None,
    }
    blockers = approval_blockers(product, {"merchant_approved": True})
    assert "gtin_assignment_unverified" in blockers


def test_admin_can_approve_only_after_identifier_verification():
    product = {
        "merchant_approved": False,
        "image_rights_approved": True,
        "provenance_status": "verified",
        "status": "draft",
        "availability_status": "InStock",
        "stock": 1,
        "selling_price_eur": 19.9,
        "sku": "LP-TEST",
        "brand": "Microsoft",
        "image_url": "/products/test.webp",
        "condition": "new",
        "gtin": "0760947037735",
        "gtin_status": "assignment_unverified",
        "mpn": None,
        "provenance_evidence_private": {
            "supplier_name": "Verified Supplier S.r.l.",
            "source_type": "authorized_distributor",
            "evidence_refs": ["private://documents/provenance-proof"],
            "reviewed_by": "admin@licenzpol.it",
            "reviewed_at": "2026-08-11T00:00:00+00:00",
        },
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
    assert approval_blockers(product, {"merchant_approved": True, "gtin_status": "verified"}) == []
