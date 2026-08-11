import asyncio
import uuid

from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient
import pytest

from services import email_outbox


def test_email_outbox_is_idempotent_claim_once_and_rejects_secrets():
    async def scenario():
        cfg = dotenv_values("backend/.env")
        client = AsyncIOMotorClient(cfg["MONGO_URL"])
        name = f"licenzpol_email_outbox_test_{uuid.uuid4().hex}"
        db = client[name]
        try:
            await email_outbox.ensure_indexes(db)
            first = await email_outbox.enqueue(
                db,
                event_key="order:ORD-1:received",
                template="order_received",
                recipient="customer@example.com",
                context={"order_reference": "ORD-1", "customer_name": "Mario"},
            )
            duplicate = await email_outbox.enqueue(
                db,
                event_key="order:ORD-1:received",
                template="order_received",
                recipient="customer@example.com",
                context={"order_reference": "ORD-1"},
            )
            assert first is True
            assert duplicate is False
            assert await db.email_outbox.count_documents({}) == 1

            claimed = await email_outbox.claim(db, "order:ORD-1:received")
            assert claimed["status"] == "sending"
            assert await email_outbox.claim(db, "order:ORD-1:received") is None

            with pytest.raises(ValueError, match="sensitive"):
                await email_outbox.enqueue(
                    db,
                    event_key="order:ORD-1:delivery",
                    template="license_delivery",
                    recipient="customer@example.com",
                    context={"license_key": "SECRET-KEY"},
                )
        finally:
            await client.drop_database(name)
            client.close()

    asyncio.run(scenario())
