"""Backend tests for Bundle Builder feature."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://silver-build.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


class TestBundleConfig:
    def test_config_shape(self, s):
        r = s.get(f"{API}/bundle/config")
        assert r.status_code == 200
        data = r.json()
        assert "slots" in data and "tiers" in data
        keys = [x["key"] for x in data["slots"]]
        for k in ["os", "office", "security", "creative", "utility"]:
            assert k in keys
        # required flags
        req = {x["key"]: x["required"] for x in data["slots"]}
        assert req["os"] and req["office"] and req["security"]
        assert not req["creative"] and not req["utility"]
        # tiers
        tiers = {t["min_items"]: t["discount"] for t in data["tiers"]}
        assert tiers[2] == 0.08 and tiers[3] == 0.12 and tiers[4] == 0.15


class TestPreset:
    def test_preset(self, s):
        r = s.get(f"{API}/bundle/preset/nuovo-pc")
        assert r.status_code == 200
        data = r.json()
        sels = data["selections"]
        assert len(sels) == 3
        slugs = {x["product_slug"]: x["variant_id"] for x in sels}
        assert slugs["windows-11-pro"] == "w11p-1pc"
        assert slugs["office-2021-professional-plus"] == "o21pp-1pc"
        assert slugs["kaspersky-standard"] == "ks-1d1y"


class TestPreview:
    def test_one_no_discount(self, s):
        r = s.post(f"{API}/bundle/preview", json={"selections": [
            {"product_slug": "windows-11-pro", "variant_id": "w11p-1pc"}]})
        assert r.status_code == 200
        d = r.json()
        assert d["count"] == 1
        assert d["discount_pct"] == 0
        assert d["discount_eur"] == 0
        assert abs(d["subtotal_eur"] - 39.90) < 0.01
        assert abs(d["total_eur"] - 39.90) < 0.01

    def test_two_8pct(self, s):
        r = s.post(f"{API}/bundle/preview", json={"selections": [
            {"product_slug": "windows-11-pro", "variant_id": "w11p-1pc"},
            {"product_slug": "office-2021-professional-plus", "variant_id": "o21pp-1pc"}]})
        d = r.json()
        assert d["discount_pct"] == 0.08
        expected_sub = 39.90 + 49.90
        assert abs(d["subtotal_eur"] - expected_sub) < 0.01
        assert abs(d["discount_eur"] - round(expected_sub * 0.08, 2)) < 0.01
        assert abs(d["total_eur"] - round(expected_sub - round(expected_sub * 0.08, 2), 2)) < 0.01

    def test_three_12pct(self, s):
        r = s.post(f"{API}/bundle/preview", json={"selections": [
            {"product_slug": "windows-11-pro", "variant_id": "w11p-1pc"},
            {"product_slug": "office-2021-professional-plus", "variant_id": "o21pp-1pc"},
            {"product_slug": "kaspersky-standard", "variant_id": "ks-1d1y"}]})
        d = r.json()
        assert d["discount_pct"] == 0.12
        sub = 39.90 + 49.90 + 19.90
        assert abs(d["subtotal_eur"] - sub) < 0.01
        assert abs(d["discount_eur"] - round(sub * 0.12, 2)) < 0.01
        assert d["total_eur"] < 100

    def test_four_15pct(self, s):
        r = s.post(f"{API}/bundle/preview", json={"selections": [
            {"product_slug": "windows-11-pro", "variant_id": "w11p-1pc"},
            {"product_slug": "office-2021-professional-plus", "variant_id": "o21pp-1pc"},
            {"product_slug": "kaspersky-standard", "variant_id": "ks-1d1y"},
            {"product_slug": "adobe-photoshop", "variant_id": "ps-1y"}]})
        d = r.json()
        assert d["discount_pct"] == 0.15
        assert d["count"] == 4

    def test_invalid_slug_dropped(self, s):
        r = s.post(f"{API}/bundle/preview", json={"selections": [
            {"product_slug": "windows-11-pro", "variant_id": "w11p-1pc"},
            {"product_slug": "does-not-exist", "variant_id": "xxx"},
            {"product_slug": "office-2021-professional-plus", "variant_id": "not-a-variant"}]})
        assert r.status_code == 200
        d = r.json()
        assert d["count"] == 1
        assert d["discount_pct"] == 0
