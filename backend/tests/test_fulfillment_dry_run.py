import asyncio
import uuid
from types import SimpleNamespace

from cryptography.fernet import Fernet
from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient

import payments
from services import email_brevo, license_inventory


def test_dry_run_fulfillment_keeps_key_reserved_and_records_secret_free_outbox(monkeypatch):
    async def scenario():
        cfg = dotenv_values("backend/.env")
        client = AsyncIOMotorClient(cfg["MONGO_URL"])
        db = client[f"licenzpol_fulfillment_dryrun_{uuid.uuid4().hex}"]
        monkeypatch.setattr(license_inventory, "LICENSE_KEY_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))
        monkeypatch.setattr(email_brevo, "EMAIL_DELIVERY_MODE", "dry-run")
        try:
            await license_inventory.ensure_indexes(db)
            from services import email_outbox
            await email_outbox.ensure_indexes(db)
            await db.products.insert_one({"sku": "LP-TEST", "stock": 0})
            await license_inventory.import_keys(db, "LP-TEST", ["REAL-SECRET-KEY"], source="test")
            await license_inventory.reserve_key(db, "LP-TEST", "ORD-DRY")
            await db.orders.insert_one({
                "reference": "ORD-DRY",
                "status": "paid",
                "email": "customer@example.com",
                "first_name": "Mario",
                "last_name": "Rossi",
                "items": [{"sku": "LP-TEST", "product_name": "Office", "quantity": 1}],
            })
            request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=db)))
            await payments._fulfil_order(request, "ORD-DRY")

            order = await db.orders.find_one({"reference": "ORD-DRY"})
            key_doc = await db.license_keys.find_one({"sku": "LP-TEST"})
            event = await db.email_outbox.find_one({"event_key": "order:ORD-DRY:license-delivery"})
            assert order["status"] == "fulfillment_pending"
            assert order["fulfillment_error_code"] == "email_dry_run"
            assert key_doc["status"] == "reserved"
            assert event["status"] == "dry_run"
            assert event["context"] == {"order_reference": "ORD-DRY"}
            assert "REAL-SECRET-KEY" not in str(event)
        finally:
            await client.drop_database(db.name)
            client.close()

    asyncio.run(scenario())
