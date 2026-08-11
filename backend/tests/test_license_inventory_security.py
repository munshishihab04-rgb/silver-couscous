import asyncio
import uuid

import pytest
from cryptography.fernet import Fernet
from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient

from services import license_inventory


def test_import_is_encrypted_deduplicated_and_idempotent(monkeypatch):
    async def scenario():
        cfg = dotenv_values("backend/.env")
        client = AsyncIOMotorClient(cfg["MONGO_URL"])
        name = f"licenzpol_inventory_test_{uuid.uuid4().hex}"
        db = client[name]
        try:
            monkeypatch.setattr(license_inventory, "LICENSE_KEY_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"), raising=False)
            await license_inventory.ensure_indexes(db)

            first = await license_inventory.import_keys(
                db,
                "LP-TEST",
                [" KEY-ONE ", "KEY-ONE", "KEY-TWO"],
                source="phase6-test",
            )
            assert first == {"imported": 2, "duplicates": 1, "rejected": 0}

            docs = await db.license_keys.find({}).to_list(length=10)
            assert len(docs) == 2
            assert all("key" not in doc and "plaintext" not in doc for doc in docs)
            assert len({doc["key_fingerprint"] for doc in docs}) == 2
            assert {license_inventory.decrypt_key(doc["key_encrypted"]) for doc in docs} == {"KEY-ONE", "KEY-TWO"}

            second = await license_inventory.import_keys(
                db,
                "LP-TEST",
                ["KEY-ONE", "KEY-TWO"],
                source="phase6-test-repeat",
            )
            assert second == {"imported": 0, "duplicates": 2, "rejected": 0}
            assert await license_inventory.available_count(db, "LP-TEST") == 2

            await db.products.insert_one({"sku": "LP-TEST", "stock": 99})
            await license_inventory.sync_product_stock(db, "LP-TEST")
            reserved = await license_inventory.reserve_key(db, "LP-TEST", "ORD-1")
            assert reserved is not None
            assert (await db.products.find_one({"sku": "LP-TEST"}))["stock"] == 1
            await license_inventory.release_reservation(db, "ORD-1")
            assert (await db.products.find_one({"sku": "LP-TEST"}))["stock"] == 2

            await db.products.insert_one({"sku": "LP-EMPTY", "stock": 99})
            await license_inventory.sync_all_product_stocks(db)
            assert (await db.products.find_one({"sku": "LP-TEST"}))["stock"] == 2
            assert (await db.products.find_one({"sku": "LP-EMPTY"}))["stock"] == 0
        finally:
            await client.drop_database(name)
            client.close()

    asyncio.run(scenario())


def test_encryption_fails_closed_without_dedicated_key(monkeypatch):
    monkeypatch.setattr(license_inventory, "LICENSE_KEY_ENCRYPTION_KEY", "", raising=False)
    with pytest.raises(RuntimeError, match="LICENSE_KEY_ENCRYPTION_KEY"):
        license_inventory.encrypt_key("SECRET")
