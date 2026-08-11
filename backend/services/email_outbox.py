"""Idempotent transactional-email outbox with no persisted secrets."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

SENSITIVE_FIELD_PARTS = {"key", "secret", "token", "password", "credential"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _assert_no_sensitive_context(value: Any, path: str = "context") -> None:
    if isinstance(value, dict):
        for field, child in value.items():
            normalised = str(field).lower()
            if any(part in normalised for part in SENSITIVE_FIELD_PARTS):
                raise ValueError(f"sensitive field is not allowed in email outbox context: {path}.{field}")
            _assert_no_sensitive_context(child, f"{path}.{field}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_no_sensitive_context(child, f"{path}[{index}]")


async def ensure_indexes(db) -> None:
    await db.email_outbox.create_index("event_key", unique=True)
    await db.email_outbox.create_index([("status", 1), ("created_at", 1)])


async def enqueue(
    db,
    *,
    event_key: str,
    template: str,
    recipient: str,
    context: dict,
) -> bool:
    _assert_no_sensitive_context(context)
    if not event_key or not template or not recipient:
        raise ValueError("event_key, template and recipient are required")
    doc = {
        "event_key": event_key,
        "template": template,
        "recipient": recipient,
        "context": context,
        "status": "queued",
        "attempts": 0,
        "created_at": _now(),
    }
    try:
        result = await db.email_outbox.update_one(
            {"event_key": event_key},
            {"$setOnInsert": doc},
            upsert=True,
        )
        return result.upserted_id is not None
    except DuplicateKeyError:
        return False


async def claim(db, event_key: str):
    return await db.email_outbox.find_one_and_update(
        {"event_key": event_key, "status": "queued"},
        {"$set": {"status": "sending", "claimed_at": _now()}, "$inc": {"attempts": 1}},
        return_document=ReturnDocument.AFTER,
    )


async def mark_sent(db, event_key: str, message_id: str, *, dry_run: bool = False) -> bool:
    result = await db.email_outbox.update_one(
        {"event_key": event_key, "status": "sending"},
        {"$set": {
            "status": "dry_run" if dry_run else "sent",
            "message_id": message_id,
            "completed_at": _now(),
        }},
    )
    return result.modified_count == 1


async def mark_failed(db, event_key: str, error_code: str) -> bool:
    result = await db.email_outbox.update_one(
        {"event_key": event_key, "status": "sending"},
        {"$set": {"status": "failed", "error_code": error_code[:100], "failed_at": _now()}},
    )
    return result.modified_count == 1
