#!/usr/bin/env python3
"""Restore an encrypted backup into an isolated MongoDB database."""
from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import os
from pathlib import Path
import sys

from bson import json_util
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
load_dotenv(BACKEND / ".env")

from backup import decrypt_backup  # noqa: E402


async def restore(path: Path, target_database: str) -> dict:
    if not target_database.startswith("licenzpol_restore_"):
        raise RuntimeError("Target database must start with licenzpol_restore_")
    compressed = decrypt_backup(path.read_bytes(), os.environ.get("BACKUP_ENCRYPTION_KEY", ""))
    payload = json_util.loads(gzip.decompress(compressed).decode("utf-8"))
    if payload.get("format") != "licenzpol-mongodb-extended-json-v1":
        raise RuntimeError("Unsupported backup format")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=3000)
    try:
        await client.drop_database(target_database)
        target = client[target_database]
        counts = {}
        for name, docs in payload["collections"].items():
            if docs:
                await target[name].insert_many(docs, ordered=True)
            counts[name] = len(docs)
        for name, expected in counts.items():
            actual = await target[name].count_documents({})
            if actual != expected:
                raise RuntimeError(f"Restore verification failed for {name}")
        return {"database": target_database, "collections": len(counts), "documents": sum(counts.values()), "verified": True}
    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path)
    parser.add_argument("--target-database", required=True)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(restore(args.backup, args.target_database)), sort_keys=True))
