import importlib


def test_clean_catalog_loader_keeps_all_rows_and_private_reference_data():
    catalog = importlib.import_module("catalog")
    products = catalog._load_csv()
    assert len(products) == 398
    assert len({product["slug"] for product in products}) == 398
    assert len({product["sku"] for product in products}) == 398
    assert all(product["gtin"] is None for product in products)
    assert all(product["mpn"] is None for product in products)
    assert sum(bool(product.get("gtin_candidate_private")) for product in products) == 395
    assert sum(bool(product.get("mpn_candidate_private")) for product in products) == 398
    assert sum(product["variants"][0]["price_eur"] is not None for product in products) == 10
    assert all(product["variants"][0]["price_eur"] is None for product in products if not product.get("pilot_candidate_private"))
    assert sum(product["variants"][0]["reference_price_private"] is None for product in products) == 1


def test_loader_marks_only_the_explicit_pilot_shortlist_without_approving_it():
    catalog = importlib.import_module("catalog")
    products = catalog._load_csv()
    pilot = [product for product in products if product.get("pilot_candidate_private")]
    assert len(pilot) == 10
    assert sorted(product["pilot_rank_private"] for product in pilot) == list(range(1, 11))
    assert all(product.get("catalog_review_status") == "pending" for product in pilot)
    assert all(product.get("merchant_approved") is False for product in pilot)
    assert {product.get("google_product_category") for product in pilot} == {"321", "5299", "5303"}
    assert all(isinstance(product.get("selling_price_eur"), float) and product["selling_price_eur"] > 0 for product in pilot)
    assert all("2025" not in product["name"] for product in pilot)


def test_ads_transparency_shortlist_is_public_preview_only_with_attested_stock_private():
    catalog = importlib.import_module("catalog")
    products = catalog._load_csv()
    observed = [product for product in products if product.get("market_observed_private")]
    assert len(observed) == 20
    assert all(product.get("catalog_visibility_status") == "published_preview" for product in observed)
    assert all(product.get("declared_stock_private") == 200 for product in observed)
    assert all(product.get("stock") == 0 and product.get("merchant_approved") is False for product in observed)
    assert all(product.get("image_rights_approved") is True for product in observed)


def test_loader_attaches_asset_fingerprints_without_approving_rights_or_provenance():
    catalog = importlib.import_module("catalog")
    products = catalog._load_csv()
    assert len(products) == 398
    assert all(product.get("provenance_evidence_private") for product in products)
    assert all(product.get("image_rights_evidence_private", {}).get("sha256") for product in products)
    assert all(product.get("provenance_status") == "unverified" for product in products)
    approved_images = [product for product in products if product.get("image_rights_approved")]
    assert len(approved_images) == 28
    assert all(product.get("image_rights_evidence_private", {}).get("rights_basis") == "owned" for product in approved_images)
    assert all(product.get("image_rights_approved") is True for product in products if product.get("pilot_candidate_private"))


def test_draft_catalog_copy_does_not_promise_unverified_fulfilment_or_originality():
    catalog = importlib.import_module("catalog")
    forbidden = ("chiave via email", "entro pochi minuti", "genuine activation", "genuine key", "email delivery", "licenza originale", "fattura elettronica ue", "no expiry")
    for product in catalog._load_csv():
        values = [
            product.get("description_it", ""), product.get("description_en", ""),
            *(product.get("whatYouGet_it") or []), *(product.get("whatYouGet_en") or []),
            *(product.get("features_it") or []), *(product.get("features_en") or []),
            *(product.get("activation_it") or []), *(product.get("activation_en") or []),
        ]
        for faq in product.get("faq") or []:
            values.extend(faq.values())
        customer_copy = " ".join(str(value) for value in values).lower()
        assert not any(phrase in customer_copy for phrase in forbidden), product["slug"]
