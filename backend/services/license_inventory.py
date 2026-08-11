"""License key inventory + delivery.

Storage collection: license_keys
{
  _id, sku, key_encrypted, status: available|reserved|delivered|released,
  reserved_for_order, delivered_at, source, notes, created_at
}

Encryption: uses a dedicated Fernet key from LICENSE_KEY_ENCRYPTION_KEY.
Plaintext keys are never persisted; deterministic HMAC fingerprints prevent duplicates.
"""

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict

from cryptography.fernet import Fernet, InvalidToken
from pymongo.errors import DuplicateKeyError

from config import LICENSE_KEY_ENCRYPTION_KEY

log = logging.getLogger("licenzpol.license")


def _fernet() -> Fernet:
    if not LICENSE_KEY_ENCRYPTION_KEY:
        raise RuntimeError("LICENSE_KEY_ENCRYPTION_KEY is required for license inventory")
    try:
        return Fernet(LICENSE_KEY_ENCRYPTION_KEY.encode("ascii"))
    except (ValueError, TypeError) as exc:
        raise RuntimeError("LICENSE_KEY_ENCRYPTION_KEY must be a valid Fernet key") from exc


def _normalise_key(value: str) -> str:
    return value.strip()


def _key_fingerprint(plaintext: str) -> str:
    if not LICENSE_KEY_ENCRYPTION_KEY:
        raise RuntimeError("LICENSE_KEY_ENCRYPTION_KEY is required for license inventory")
    return hmac.new(
        LICENSE_KEY_ENCRYPTION_KEY.encode("ascii"),
        _normalise_key(plaintext).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


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
    await db.license_keys.create_index("key_fingerprint", unique=True)


async def import_keys(db, sku: str, keys: List[str], source: str = "manual") -> Dict[str, int]:
    """Idempotently import encrypted keys without persisting plaintext."""
    if not sku or not sku.strip():
        raise ValueError("sku is required")
    _fernet()  # fail closed before processing any input
    now = datetime.now(timezone.utc).isoformat()
    report = {"imported": 0, "duplicates": 0, "rejected": 0}
    seen: set[str] = set()
    for raw in keys:
        plaintext = _normalise_key(str(raw or ""))
        if not plaintext:
            report["rejected"] += 1
            continue
        fingerprint = _key_fingerprint(plaintext)
        if fingerprint in seen:
            report["duplicates"] += 1
            continue
        seen.add(fingerprint)
        doc = {
            "sku": sku.strip(),
            "key_encrypted": encrypt_key(plaintext),
            "key_fingerprint": fingerprint,
            "status": "available",
            "reserved_for_order": None,
            "delivered_at": None,
            "source": (source or "manual").strip()[:200],
            "created_at": now,
        }
        try:
            result = await db.license_keys.update_one(
                {"key_fingerprint": fingerprint},
                {"$setOnInsert": doc},
                upsert=True,
            )
            if result.upserted_id is None:
                report["duplicates"] += 1
            else:
                report["imported"] += 1
        except DuplicateKeyError:
            report["duplicates"] += 1
    return report


async def available_count(db, sku: str) -> int:
    return await db.license_keys.count_documents({"sku": sku, "status": "available"})


async def sync_product_stock(db, sku: str) -> int:
    count = await available_count(db, sku)
    await db.products.update_many({"sku": sku}, {"$set": {"stock": count}})
    return count


async def sync_all_product_stocks(db) -> Dict[str, int]:
    await db.products.update_many({}, {"$set": {"stock": 0}})
    counts: Dict[str, int] = {}
    async for row in db.license_keys.aggregate([
        {"$match": {"status": "available"}},
        {"$group": {"_id": "$sku", "count": {"$sum": 1}}},
    ]):
        sku = row["_id"]
        count = int(row["count"])
        counts[sku] = count
        await db.products.update_many({"sku": sku}, {"$set": {"stock": count}})
    return counts


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
    else:
        await sync_product_stock(db, sku)
    return doc


async def release_reservation(db, order_reference: str) -> int:
    query = {"reserved_for_order": order_reference, "status": "reserved"}
    skus = await db.license_keys.distinct("sku", query)
    r = await db.license_keys.update_many(
        query,
        {"$set": {
            "status": "available",
            "reserved_for_order": None,
            "released_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    for sku in skus:
        await sync_product_stock(db, sku)
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
