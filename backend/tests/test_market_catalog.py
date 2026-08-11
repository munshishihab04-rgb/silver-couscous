from market_catalog import catalog_display_failures, dedupe_ads_products


def test_ads_transparency_rows_are_deduplicated_by_catalog_product():
    rows = [
        {"catalog_gtin": "0889842905892", "product_title": "Ad A", "ads_item_ids": "1"},
        {"catalog_gtin": "0889842905892", "product_title": "Ad B", "ads_item_ids": "2"},
    ]
    products = [{"slug": "windows-11-pro", "gtin_candidate_private": "0889842905892", "name": "Windows 11 Pro"}]
    result = dedupe_ads_products(rows, products)
    assert len(result) == 1
    assert result[0]["creative_titles"] == ["Ad A", "Ad B"]
    assert result[0]["checksum_valid"] is True


def test_public_preview_never_implies_offer_readiness():
    product = {
        "catalog_visibility_status": "published_preview",
        "name": "Example",
        "brand": "Vendor",
        "image_url": "/products/example.webp",
        "image_rights_approved": True,
        "image_rights_evidence_private": {
            "asset_path": "/products/example.webp",
            "sha256": "a" * 64,
            "width": 1200,
            "height": 1200,
            "rights_basis": "owned",
            "evidence_refs": ["private://documents/generated"],
            "reviewed_by": "automation:hermes-agent",
            "reviewed_at": "2026-08-11T00:00:00+00:00",
        },
        "merchant_approved": False,
        "stock": 0,
        "declared_stock_private": 200,
    }
    assert catalog_display_failures(product) == []
    assert product["merchant_approved"] is False
    assert product["stock"] == 0
