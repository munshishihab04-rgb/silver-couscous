#!/usr/bin/env python3
"""Create and verify an encrypted Extended JSON backup of the local MongoDB."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import sys

from bson import json_util
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
load_dotenv(BACKEND / ".env")

from backup import decrypt_backup, encrypt_backup  # noqa: E402

OUTPUT_DIR = ROOT / ".runtime" / "backups"


async def create_backup() -> dict:
    key = os.environ.get("BACKUP_ENCRYPTION_KEY", "")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=3000)
    db = client[os.environ["DB_NAME"]]
    try:
        await db.command("ping")
        names = sorted(name for name in await db.list_collection_names() if not name.startswith("system."))
        collections = {}
        counts = {}
        for name in names:
            docs = await db[name].find({}).to_list(length=None)
            collections[name] = docs
            counts[name] = len(docs)
        payload = {
            "format": "licenzpol-mongodb-extended-json-v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database": os.environ["DB_NAME"],
            "collections": collections,
        }
        raw = json_util.dumps(payload, ensure_ascii=False).encode("utf-8")
        compressed = gzip.compress(raw, compresslevel=9)
        encrypted = encrypt_backup(compressed, key)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = OUTPUT_DIR / f"licenzpol-{stamp}.json.gz.fernet"
        path.write_bytes(encrypted)
        path.chmod(0o600)

        verified = json_util.loads(gzip.decompress(decrypt_backup(path.read_bytes(), key)).decode("utf-8"))
        if verified.get("format") != payload["format"]:
            raise RuntimeError("Backup verification failed")

        backups = sorted(OUTPUT_DIR.glob("licenzpol-*.json.gz.fernet"), reverse=True)
        for stale in backups[14:]:
            stale.unlink()
        return {
            "path": str(path),
            "collections": len(names),
            "documents": sum(counts.values()),
            "bytes": path.stat().st_size,
            "verified": True,
        }
    finally:
        client.close()


if __name__ == "__main__":
    print(json.dumps(asyncio.run(create_backup()), sort_keys=True))
