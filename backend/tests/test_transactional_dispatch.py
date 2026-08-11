import asyncio
import uuid

from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient

from services import email_brevo, email_outbox, transactional_dispatch


def test_order_received_event_dispatches_once_in_dry_run(monkeypatch):
    async def scenario():
        cfg = dotenv_values("backend/.env")
        client = AsyncIOMotorClient(cfg["MONGO_URL"])
        db = client[f"licenzpol_dispatch_test_{uuid.uuid4().hex}"]
        monkeypatch.setattr(email_brevo, "EMAIL_DELIVERY_MODE", "dry-run")
        try:
            await email_outbox.ensure_indexes(db)
            await email_outbox.enqueue(
                db,
                event_key="order:ORD-1:received",
                template="order_received",
                recipient="customer@example.com",
                context={
                    "customer_name": "Mario",
                    "order_reference": "ORD-1",
                    "total_eur": 10.0,
                    "items": [{"product_name": "Office", "variant_label": "1 PC", "quantity": 1, "unit_price_eur": 10.0}],
                },
            )
            first = await transactional_dispatch.dispatch(db, "order:ORD-1:received")
            second = await transactional_dispatch.dispatch(db, "order:ORD-1:received")
            assert first["status"] == "dry_run"
            assert second["status"] == "already_processed"
            saved = await db.email_outbox.find_one({"event_key": "order:ORD-1:received"})
            assert saved["status"] == "dry_run"
            assert saved["message_id"].startswith("dry-run:")
        finally:
            await client.drop_database(db.name)
            client.close()

    asyncio.run(scenario())
