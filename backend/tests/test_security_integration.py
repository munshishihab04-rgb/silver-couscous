from fastapi.testclient import TestClient
from dotenv import dotenv_values
from pymongo import MongoClient
import time

from server import app
from config import JWT_SECRET
from form_challenge import issue_form_challenge


def test_health_security_headers_trusted_hosts_and_payload_limit():
    with TestClient(app, base_url="http://testserver") as client:
        health = client.get("/api/health", headers={"X-Forwarded-Proto": "https"})
        assert health.status_code == 200
        assert health.json()["database"] == "ok"
        assert health.headers["x-content-type-options"] == "nosniff"
        assert health.headers["x-frame-options"] == "DENY"
        assert "default-src 'self'" in health.headers["content-security-policy"]
        assert "strict-transport-security" not in health.headers
        assert len(health.headers["x-request-id"]) == 32

        oversized = client.post(
            "/api/support",
            content=b"x" * 1_048_577,
            headers={"Content-Type": "application/json"},
        )
        assert oversized.status_code == 413
        assert oversized.headers["x-content-type-options"] == "nosniff"

        rejected = client.get("/api/health", headers={"Host": "attacker.invalid"})
        assert rejected.status_code == 400

        token = issue_form_challenge("support", JWT_SECRET, now=int(time.time()) - 2)
        payload = {
            "email": "challenge-qa@example.invalid",
            "subject": "single use",
            "message": "synthetic integration test",
            "language": "it",
            "form_token": token,
            "website": "",
        }
        first = client.post("/api/support", json=payload)
        second = client.post("/api/support", json=payload)
        assert first.status_code == 200
        assert second.status_code == 400

    cfg = dotenv_values("backend/.env")
    mongo = MongoClient(cfg["MONGO_URL"])
    mongo[cfg["DB_NAME"]].support_messages.delete_one({"id": first.json()["id"]})
    mongo.close()
