import asyncio
import uuid
from types import SimpleNamespace

from cryptography.fernet import Fernet
from dotenv import dotenv_values
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from merchant_admin import LicenseImportBody, merchant_import_licenses
from services import license_inventory


def test_admin_inventory_import_rejects_unknown_sku_and_audits_counts(monkeypatch):
    async def scenario():
        cfg = dotenv_values("backend/.env")
        client = AsyncIOMotorClient(cfg["MONGO_URL"])
        name = f"licenzpol_inventory_api_test_{uuid.uuid4().hex}"
        db = client[name]

        async def reload_products():
            return None

        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=db, reload_products=reload_products)))
        user = {"_id": "admin-1", "email": "admin@example.com"}
        monkeypatch.setattr(license_inventory, "LICENSE_KEY_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))
        try:
            await license_inventory.ensure_indexes(db)
            try:
                await merchant_import_licenses(
                    LicenseImportBody(sku="UNKNOWN", keys=["X"]), request, user
                )
                assert False, "unknown SKU import must fail"
            except HTTPException as exc:
                assert exc.status_code == 404

            await db.products.insert_one({"sku": "LP-REAL", "stock": 0})
            result = await merchant_import_licenses(
                LicenseImportBody(sku="LP-REAL", keys=["KEY-A", "KEY-A", "KEY-B"], source="supplier-batch"),
                request,
                user,
            )
            assert result == {"imported": 2, "duplicates": 1, "rejected": 0, "available_now": 2}
            product = await db.products.find_one({"sku": "LP-REAL"})
            assert product["stock"] == 2
            audit = await db.merchant_audit.find_one({"action": "license_import"})
            assert audit["counts"] == {"imported": 2, "duplicates": 1, "rejected": 0}
            assert "keys" not in audit
        finally:
            await client.drop_database(name)
            client.close()

    asyncio.run(scenario())
