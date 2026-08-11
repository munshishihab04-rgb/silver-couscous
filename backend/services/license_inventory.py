"""License key inventory + delivery.

Storage collection: license_keys
{
  _id, sku, key_encrypted, status: available|reserved|delivered|released,
  reserved_for_order, delivered_at, source, notes, created_at
}

Encryption: uses Fernet symmetric encryption with a key derived from JWT_SECRET.
"""

import base64
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict

from cryptography.fernet import Fernet, InvalidToken

from config import JWT_SECRET

log = logging.getLogger("licenzpol.license")


def _fernet() -> Fernet:
    seed = (JWT_SECRET or "licenzpol-dev-secret-please-change").encode("utf-8")
    digest = hashlib.sha256(seed).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_key(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_key(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken:
        raise ValueError("Invalid encrypted key token")


async def ensure_indexes(db):
    await db.license_keys.create_index("sku")
    await db.license_keys.create_index([("sku", 1), ("status", 1)])
    await db.license_keys.create_index("reserved_for_order")


async def import_keys(db, sku: str, keys: List[str], source: str = "manual") -> int:
    """Bulk-import raw license keys for a SKU. Returns number inserted."""
    if not keys:
        return 0
    now = datetime.now(timezone.utc).isoformat()
    docs = [{
        "sku": sku,
        "key_encrypted": encrypt_key(k.strip()),
        "status": "available",
        "reserved_for_order": None,
        "delivered_at": None,
        "source": source,
        "created_at": now,
    } for k in keys if k.strip()]
    if not docs:
        return 0
    r = await db.license_keys.insert_many(docs)
    return len(r.inserted_ids)


async def available_count(db, sku: str) -> int:
    return await db.license_keys.count_documents({"sku": sku, "status": "available"})


async def reserve_key(db, sku: str, order_reference: str) -> Optional[Dict]:
    """Atomically reserve one available key for a SKU. Returns doc or None."""
    doc = await db.license_keys.find_one_and_update(
        {"sku": sku, "status": "available"},
        {"$set": {
            "status": "reserved",
            "reserved_for_order": order_reference,
            "reserved_at": datetime.now(timezone.utc).isoformat(),
        }},
        return_document=True,
    )
    if not doc:
        log.warning("reserve_key: no key available for sku=%s", sku)
    return doc


async def release_reservation(db, order_reference: str) -> int:
    r = await db.license_keys.update_many(
        {"reserved_for_order": order_reference, "status": "reserved"},
        {"$set": {
            "status": "available",
            "reserved_for_order": None,
            "released_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return r.modified_count


async def mark_delivered(db, order_reference: str) -> int:
    r = await db.license_keys.update_many(
        {"reserved_for_order": order_reference, "status": "reserved"},
        {"$set": {
            "status": "delivered",
            "delivered_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return r.modified_count


async def get_keys_for_order(db, order_reference: str) -> List[Dict]:
    out = []
    async for doc in db.license_keys.find({"reserved_for_order": order_reference}):
        doc.pop("_id", None)
        out.append(doc)
    return out
