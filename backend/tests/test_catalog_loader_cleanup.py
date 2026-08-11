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
    assert all(product["variants"][0]["price_eur"] is None for product in products)
    assert sum(product["variants"][0]["reference_price_private"] is None for product in products) == 1


def test_loader_attaches_asset_fingerprints_without_approving_rights_or_provenance():
    catalog = importlib.import_module("catalog")
    products = catalog._load_csv()
    assert len(products) == 398
    assert all(product.get("provenance_evidence_private") for product in products)
    assert all(product.get("image_rights_evidence_private", {}).get("sha256") for product in products)
    assert all(product.get("provenance_status") == "unverified" for product in products)
    assert all(product.get("image_rights_approved") is False for product in products)


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
