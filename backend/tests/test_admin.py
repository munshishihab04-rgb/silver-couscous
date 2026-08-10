"""Backend tests for LicenzPol admin panel (JWT auth, products, customers,
tickets, CMS pages, settings, users, analytics)."""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://software-made-simple.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me")


# ------------------- Fixtures -------------------

@pytest.fixture(scope="session")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def token(api_client):
    r = api_client.post(f"{API}/admin/auth/login",
                        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"login failed {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data and "user" in data
    return data["token"]


@pytest.fixture(scope="session")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ------------------- Auth -------------------

class TestAuth:
    def test_login_success(self, api_client):
        r = api_client.post(f"{API}/admin/auth/login",
                            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["token"], str) and len(d["token"]) > 20
        assert d["user"]["email"] == ADMIN_EMAIL
        assert d["user"]["role"] == "admin"

    def test_login_wrong_password(self, api_client):
        r = api_client.post(f"{API}/admin/auth/login",
                            json={"email": ADMIN_EMAIL, "password": "wrongpass"})
        # 401 expected; may be 429 if lockout triggered by prior brute test run — accept both
        assert r.status_code in (401, 429)

    def test_me_with_token(self, api_client, auth_headers):
        r = api_client.get(f"{API}/admin/auth/me", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["user"]["email"] == ADMIN_EMAIL

    def test_me_without_token(self, api_client):
        r = requests.get(f"{API}/admin/auth/me")
        assert r.status_code == 401


# ------------------- Admin endpoint auth guard -------------------

class TestAuthGuard:
    endpoints = [
        "/admin/products", "/admin/customers", "/admin/tickets",
        "/admin/pages", "/admin/settings", "/admin/users",
        "/admin/analytics/overview",
    ]

    @pytest.mark.parametrize("path", endpoints)
    def test_requires_auth(self, path):
        r = requests.get(f"{API}{path}")
        assert r.status_code == 401, f"{path} did not return 401 (got {r.status_code})"


# ------------------- Products -------------------

class TestProducts:
    def test_list_products(self, api_client, auth_headers):
        r = api_client.get(f"{API}/admin/products", headers=auth_headers)
        assert r.status_code == 200
        d = r.json()
        assert "total" in d and "items" in d
        # migrated CSV should be ~397 products
        assert d["total"] >= 300, f"expected 300+ products, got {d['total']}"

    def test_create_get_update_delete(self, api_client, auth_headers):
        slug = f"test-prod-{uuid.uuid4().hex[:8]}"
        body = {
            "slug": slug, "name": "TEST_Product", "category": "utility",
            "brand": "TESTBRAND", "tagline_it": "t", "tagline_en": "t",
            "variants": [{"id": "v1", "edition": "Std", "duration_months": 12, "devices": 1, "price_eur": 9.99}],
        }
        # Create
        r = api_client.post(f"{API}/admin/products", json=body, headers=auth_headers)
        assert r.status_code == 200, r.text
        assert r.json()["slug"] == slug

        # Duplicate → 409
        r2 = api_client.post(f"{API}/admin/products", json=body, headers=auth_headers)
        assert r2.status_code == 409

        # Get
        r3 = api_client.get(f"{API}/admin/products/{slug}", headers=auth_headers)
        assert r3.status_code == 200
        assert r3.json()["name"] == "TEST_Product"

        # Patch
        r4 = api_client.patch(f"{API}/admin/products/{slug}",
                              json={"name": "TEST_Updated"}, headers=auth_headers)
        assert r4.status_code == 200
        assert r4.json()["name"] == "TEST_Updated"

        # Verify persisted
        r5 = api_client.get(f"{API}/admin/products/{slug}", headers=auth_headers)
        assert r5.json()["name"] == "TEST_Updated"

        # Delete
        r6 = api_client.delete(f"{API}/admin/products/{slug}", headers=auth_headers)
        assert r6.status_code == 200

        # 404 after delete
        r7 = api_client.get(f"{API}/admin/products/{slug}", headers=auth_headers)
        assert r7.status_code == 404


# ------------------- CMS Pages -------------------

class TestPages:
    def test_list_default_pages(self, api_client, auth_headers):
        r = api_client.get(f"{API}/admin/pages", headers=auth_headers)
        assert r.status_code == 200
        slugs = {p["slug"] for p in r.json()}
        for expected in ["privacy", "terms", "cookies", "transparency"]:
            assert expected in slugs, f"missing default page {expected}"

    def test_upsert_page(self, api_client, auth_headers):
        slug = "software-made-simple"
        body = {"title_it": "SMS IT", "title_en": "SMS EN",
                "content_it": "# it", "content_en": "# en"}
        r = api_client.put(f"{API}/admin/pages/{slug}", json=body, headers=auth_headers)
        assert r.status_code == 200
        # public read
        r2 = requests.get(f"{API}/pages/{slug}")
        assert r2.status_code == 200
        assert r2.json()["title_it"] == "SMS IT"


# ------------------- Settings -------------------

class TestSettings:
    def test_get_admin_settings(self, api_client, auth_headers):
        r = api_client.get(f"{API}/admin/settings", headers=auth_headers)
        assert r.status_code == 200
        assert r.json().get("key") == "site"

    def test_patch_settings(self, api_client, auth_headers):
        val = f"G-TEST{uuid.uuid4().hex[:6].upper()}"
        r = api_client.patch(f"{API}/admin/settings",
                             json={"ga4_measurement_id": val}, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["ga4_measurement_id"] == val
        # Public settings must reflect it
        r2 = requests.get(f"{API}/settings")
        assert r2.status_code == 200
        pub = r2.json()
        assert pub["ga4_measurement_id"] == val
        # Sensitive fields must NOT be exposed
        assert "password_hash" not in pub
        assert "key" not in pub  # only PUBLIC_SETTINGS_FIELDS
        # Cleanup: reset
        api_client.patch(f"{API}/admin/settings",
                        json={"ga4_measurement_id": ""}, headers=auth_headers)


# ------------------- Admin users -------------------

class TestAdminUsers:
    def test_create_list_delete_admin(self, api_client, auth_headers):
        email = f"test_{uuid.uuid4().hex[:6]}@example.com"
        r = api_client.post(f"{API}/admin/users",
                            json={"email": email, "password": "TestPass123!", "name": "T"},
                            headers=auth_headers)
        assert r.status_code == 200, r.text
        uid = r.json()["id"]

        r2 = api_client.get(f"{API}/admin/users", headers=auth_headers)
        assert r2.status_code == 200
        emails = [u["email"] for u in r2.json()]
        assert email in emails
        assert ADMIN_EMAIL in emails

        r3 = api_client.delete(f"{API}/admin/users/{uid}", headers=auth_headers)
        assert r3.status_code == 200


# ------------------- Customers & Tickets -------------------

class TestCustomersAndTickets:
    def test_customers_list(self, api_client, auth_headers):
        r = api_client.get(f"{API}/admin/customers", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_ticket_flow(self, api_client, auth_headers):
        # Create a support message via public endpoint
        r = requests.post(f"{API}/support", json={
            "email": "TEST_ticket@example.com",
            "subject": "TEST_subject", "message": "TEST_msg",
        })
        assert r.status_code == 200
        tid = r.json()["id"]

        # Admin list
        r2 = api_client.get(f"{API}/admin/tickets", headers=auth_headers)
        assert r2.status_code == 200
        assert any(t.get("id") == tid for t in r2.json())

        # Patch status
        r3 = api_client.patch(f"{API}/admin/tickets/{tid}",
                              json={"status": "closed", "admin_notes": "done"},
                              headers=auth_headers)
        assert r3.status_code == 200


# ------------------- Public settings & pages -------------------

class TestPublic:
    def test_public_settings_shape(self):
        r = requests.get(f"{API}/settings")
        assert r.status_code == 200
        d = r.json()
        for k in ("logo_text", "ga4_measurement_id", "gtm_container_id",
                  "meta_pixel_id", "custom_head_html", "custom_body_html",
                  "site_title", "site_description"):
            assert k in d


# ------------------- Analytics -------------------

class TestAnalytics:
    def test_track_and_overview(self, api_client, auth_headers):
        vid = f"TEST_vid_{uuid.uuid4().hex[:8]}"
        for evt in [
            {"visitor_id": vid, "event_type": "page_view", "path": "/", "device_type": "desktop", "referrer": "https://google.com/"},
            {"visitor_id": vid, "event_type": "product_view", "path": "/p/x", "product_slug": "windows-11-pro", "device_type": "mobile"},
            {"visitor_id": vid, "event_type": "add_to_cart", "product_slug": "windows-11-pro"},
            {"visitor_id": vid, "event_type": "checkout_start", "path": "/checkout"},
        ]:
            r = requests.post(f"{API}/analytics/track", json=evt)
            assert r.status_code == 200

        r2 = api_client.get(f"{API}/admin/analytics/overview?range=7d", headers=auth_headers)
        assert r2.status_code == 200
        d = r2.json()
        for k in ("kpis", "top_pages", "top_products", "timeseries", "referrers", "devices"):
            assert k in d
        assert d["kpis"]["events"] >= 4
        assert d["kpis"]["page_views"] >= 1


# ------------------- Brute-force lockout -------------------

class TestBruteForce:
    def test_lockout_after_5_fails(self, api_client):
        email = f"bf_{uuid.uuid4().hex[:6]}@example.com"
        # 5 fails
        codes = []
        for _ in range(5):
            r = api_client.post(f"{API}/admin/auth/login",
                                json={"email": email, "password": "x"})
            codes.append(r.status_code)
        # 6th should be 429
        r6 = api_client.post(f"{API}/admin/auth/login",
                             json={"email": email, "password": "x"})
        assert r6.status_code == 429, f"expected 429, got {r6.status_code}; prior codes={codes}"
