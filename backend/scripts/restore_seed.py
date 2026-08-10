#!/usr/bin/env python3
"""Restore the public LicenzPol seed into the MongoDB configured by backend/.env."""
from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
SEED_DIR = ROOT / "database" / "seed"
BACKEND_ENV = ROOT / "backend" / ".env"

load_dotenv(BACKEND_ENV)

import os

client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]

spec = {
    "products": "slug",
    "pages": "slug",
    "settings": "key",
}

for collection, key in spec.items():
    path = SEED_DIR / f"{collection}.json"
    docs = json.loads(path.read_text(encoding="utf-8"))
    for doc in docs:
        if key not in doc:
            raise ValueError(f"Missing {key!r} in {path}")
        db[collection].replace_one({key: doc[key]}, doc, upsert=True)
    print(f"{collection}: restored {len(docs)}")

print("Seed restore completed")
