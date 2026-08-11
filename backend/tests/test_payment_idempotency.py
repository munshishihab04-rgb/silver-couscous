import asyncio
import uuid
from types import SimpleNamespace

from cryptography.fernet import Fernet
from dotenv import dotenv_values
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import pytest

import payments
from payments import can_transition, claim_fulfillment, claim_payment_initialization, reset_payment_initialization, sanitize_psp_operation, should_finalize_delivery, should_initialize_payment
from services import license_inventory
from order_access import hash_order_token


def test_psp_event_persistence_discards_sensitive_provider_fields():
    sanitized = sanitize_psp_operation({
        "orderId": "ORD-1",
        "operationId": "OP-1",
        "operationResult": "AUTHORIZED",
        "cardNumber": "4111111111111111",
        "securityToken": "secret",
        "customerEmail": "customer@example.com",
    })
    assert sanitized == {"orderId": "ORD-1", "operationId": "OP-1", "operationResult": "AUTHORIZED"}


def test_payment_initialization_is_idempotent_after_first_attempt():
    assert should_initialize_payment({"status": "draft"}) is True
    assert should_initialize_payment({"status": "demo_confirmed"}) is True
    assert should_initialize_payment({"status": "pending_payment"}) is False
    assert should_initialize_payment({"status": "pending_payment", "psp_order_id": "PSP-1"}) is False
    assert should_initialize_payment({"status": "paid"}) is False


def test_dry_run_delivery_never_consumes_real_inventory():
    assert should_finalize_delivery([]) is False
    assert should_finalize_delivery(["dry-run:abc"]) is False
    assert should_finalize_delivery(["brevo-message-id"]) is True


def test_order_state_machine_rejects_regressions_and_duplicate_terminal_changes():
    assert can_transition("pending_payment", "paid") is True
    assert can_transition("pending_payment", "failed") is True
    assert can_transition("paid", "fulfilled") is True
    assert can_transition("paid", "fulfillment_processing") is True
    assert can_transition("fulfillment_processing", "fulfillment_pending") is True
    assert can_transition("fulfilled", "refunded") is True
    assert can_transition("fulfilled", "failed") is False
    assert can_transition("paid", "pending_payment") is False
    assert can_transition("paid", "paid") is True


def test_fulfillment_claim_is_atomic_and_single_consumer():
    async def scenario():
        cfg = dotenv_values("backend/.env")
        client = AsyncIOMotorClient(cfg["MONGO_URL"])
        db = client[f"licenzpol_fulfillment_claim_{uuid.uuid4().hex}"]
        try:
            await db.orders.insert_one({"reference": "ORD-1", "status": "paid"})
            first = await claim_fulfillment(db, "ORD-1")
            second = await claim_fulfillment(db, "ORD-1")
            assert first["status"] == "fulfillment_processing"
            assert second is None
            assert (await db.orders.find_one({"reference": "ORD-1"}))["fulfillment_attempts"] == 1
        finally:
            await client.drop_database(db.name)
            client.close()

    asyncio.run(scenario())


def test_payment_initialization_claim_is_atomic():
    async def scenario():
        cfg = dotenv_values("backend/.env")
        client = AsyncIOMotorClient(cfg["MONGO_URL"])
        db = client[f"licenzpol_payment_claim_{uuid.uuid4().hex}"]
        try:
            await db.orders.insert_one({"reference": "ORD-PAY", "status": "draft"})
            first = await claim_payment_initialization(db, "ORD-PAY", "draft")
            second = await claim_payment_initialization(db, "ORD-PAY", "draft")
            assert first is True
            assert second is False
            assert (await db.orders.find_one({"reference": "ORD-PAY"}))["status"] == "payment_initializing"
            await reset_payment_initialization(db, "ORD-PAY", "draft")
            assert (await db.orders.find_one({"reference": "ORD-PAY"}))["status"] == "draft"
            assert await claim_payment_initialization(db, "ORD-PAY", "draft") is True
        finally:
            await client.drop_database(db.name)
            client.close()

    asyncio.run(scenario())


def test_provider_failure_releases_inventory_and_resets_payment_claim(monkeypatch):
    async def scenario():
        cfg = dotenv_values("backend/.env")
        client = AsyncIOMotorClient(cfg["MONGO_URL"])
        db = client[f"licenzpol_payment_failure_{uuid.uuid4().hex}"]
        monkeypatch.setattr(license_inventory, "LICENSE_KEY_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))
        monkeypatch.setattr(payments, "COMMERCE_ENABLED", True)
        monkeypatch.setattr(payments.nexi_xpay, "is_configured", lambda: True)

        async def provider_failure(**kwargs):
            raise RuntimeError("provider unavailable")

        monkeypatch.setattr(payments.nexi_xpay, "create_hosted_payment", provider_failure)
        try:
            await license_inventory.ensure_indexes(db)
            await db.products.insert_one({"sku": "LP-PAY", "stock": 0})
            await license_inventory.import_keys(db, "LP-PAY", ["KEY-PAY"], source="test")
            await db.orders.insert_one({
                "reference": "ORD-FAIL",
                "status": "draft",
                "access_token_hash": hash_order_token("order-token"),
                "items": [{"sku": "LP-PAY", "quantity": 1, "product_name": "Office"}],
                "total_eur": 10.0,
            })
            request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=db)))
            with pytest.raises(HTTPException) as exc:
                await payments.create_payment_for_order("ORD-FAIL", request, "order-token")
            assert exc.value.status_code == 502
            assert (await db.orders.find_one({"reference": "ORD-FAIL"}))["status"] == "draft"
            assert (await db.license_keys.find_one({"sku": "LP-PAY"}))["status"] == "available"
        finally:
            await client.drop_database(db.name)
            client.close()

    asyncio.run(scenario())
