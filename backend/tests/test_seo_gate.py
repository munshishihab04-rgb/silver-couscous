from exports_seo import robots_body, sitemap_product_query


def test_staging_robots_disallow_all_crawlers():
    body = robots_body("staging", "https://preview.example/sitemap.xml")
    assert "Disallow: /" in body
    assert "Allow: /" not in body


def test_production_soft_launch_remains_noindex_until_explicitly_enabled():
    body = robots_body("production", "https://licenzpol.it/sitemap.xml", indexing_enabled=False)
    assert "Disallow: /" in body
    assert "Allow: /" not in body


def test_production_robots_allow_public_pages_and_block_private_routes():
    body = robots_body("production", "https://licenzpol.it/sitemap.xml")
    assert "Allow: /" in body
    assert "Disallow: /admin" in body
    assert "Disallow: /checkout" in body
    assert "https://licenzpol.it/sitemap.xml" in body


def test_staging_sitemap_uses_an_impossible_product_query():
    assert sitemap_product_query("staging") == {"_id": {"$exists": False}}


def test_production_sitemap_only_queries_approved_candidates():
    assert sitemap_product_query("production") == {"merchant_approved": True}
