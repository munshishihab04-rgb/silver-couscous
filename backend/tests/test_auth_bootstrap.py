import asyncio
import uuid

from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient

from auth import hash_password, seed_admin, verify_password


def test_admin_bootstrap_never_resets_existing_password_from_environment(monkeypatch):
    async def scenario():
        cfg = dotenv_values("backend/.env")
        client = AsyncIOMotorClient(cfg["MONGO_URL"])
        db = client[f"licenzpol_auth_bootstrap_{uuid.uuid4().hex}"]
        monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
        monkeypatch.setenv("ADMIN_PASSWORD", "new-environment-password")
        try:
            original_hash = hash_password("existing-password")
            await db.admin_users.insert_one({"email": "admin@example.com", "password_hash": original_hash, "role": "admin"})
            await seed_admin(db)
            saved = await db.admin_users.find_one({"email": "admin@example.com"})
            assert saved["password_hash"] == original_hash
            assert verify_password("existing-password", saved["password_hash"])
            assert not verify_password("new-environment-password", saved["password_hash"])
        finally:
            await client.drop_database(db.name)
            client.close()

    asyncio.run(scenario())
