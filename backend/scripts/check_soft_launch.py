#!/usr/bin/env python3
"""Fail-closed smoke test for the definitive-domain soft launch."""
from __future__ import annotations

import argparse
import json
from urllib.parse import urlparse

import requests


def check(base: str, *, production: bool = True, indexing_enabled: bool = False) -> dict:
    base = base.rstrip("/")
    host = urlparse(base).hostname
    session = requests.Session()

    health = session.get(base + "/api/health", timeout=20)
    health.raise_for_status()
    assert health.json()["database"] == "ok"
    assert health.headers["X-Content-Type-Options"] == "nosniff"
    assert health.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in health.headers["Content-Security-Policy"]
    if production:
        assert health.headers["Strict-Transport-Security"].startswith("max-age=")
    else:
        assert "Strict-Transport-Security" not in health.headers

    products = session.get(base + "/api/products?limit=500", timeout=20)
    products.raise_for_status()
    catalog = products.json()
    assert catalog["total"] == 20

    payment = session.get(base + "/api/payments/config", timeout=20)
    payment.raise_for_status()
    assert payment.json()["commerce_enabled"] is False

    feed = session.get(base + "/api/merchant/feed.xml", timeout=20)
    feed.raise_for_status()
    assert "<item>" not in feed.text

    robots = session.get(base + "/robots.txt", timeout=20)
    robots.raise_for_status()
    if production and indexing_enabled:
        assert "Disallow: /admin" in robots.text
        assert f"https://{host}/sitemap.xml" in robots.text
    else:
        assert "Disallow: /" in robots.text

    unauthorized = session.get(base + "/api/admin/auth/me", timeout=20)
    assert unauthorized.status_code == 401
    assert unauthorized.headers.get("Cache-Control") == "no-store"

    return {
        "base_url": base,
        "health": "ok",
        "catalog": catalog["total"],
        "commerce_enabled": False,
        "merchant_feed_items": 0,
        "hsts": production,
        "robots": "indexable" if production and indexing_enabled else "noindex",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument("--staging", action="store_true", help="expect staging transport headers")
    parser.add_argument("--indexable", action="store_true", help="expect production robots and sitemap")
    args = parser.parse_args()
    print(json.dumps(check(args.base_url, production=not args.staging, indexing_enabled=args.indexable), sort_keys=True))
