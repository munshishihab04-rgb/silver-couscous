#!/usr/bin/env python3
"""Dry-run/apply a private CSV inventory import without printing license keys."""
from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from collections import defaultdict

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
load_dotenv(BACKEND / ".env")

from inventory_import import analyse_rows  # noqa: E402
from services import license_inventory  # noqa: E402


def private_input_path(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    private_root = (ROOT / ".runtime").resolve()
    if private_root not in path.parents:
        raise argparse.ArgumentTypeError("Inventory input must be stored under .runtime/")
    return path


async def run(path: Path, apply: bool) -> dict:
    import os

    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    try:
        known_skus = set(await db.products.distinct("sku"))
        with path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        valid, report = analyse_rows(rows, known_skus)
        output = {"mode": "apply" if apply else "dry-run", **report}
        if not apply:
            return output
        if report["unknown_sku"] or report["blank_or_invalid"]:
            raise RuntimeError("Import blocked: CSV contains unknown SKUs or blank/invalid rows")

        grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
        for row in valid:
            grouped[(row["sku"], row["source"])].append(row["key"])
        totals = {"imported": 0, "duplicates": report["duplicates_in_file"], "rejected": 0}
        for (sku, source), keys in grouped.items():
            result = await license_inventory.import_keys(db, sku, keys, source=source)
            for field in totals:
                totals[field] += result[field]
            available = await license_inventory.available_count(db, sku)
            await db.products.update_many({"sku": sku}, {"$set": {"stock": available}})
        await db.merchant_audit.insert_one({
            "action": "private_inventory_csv_import",
            "file_name": path.name,
            "counts": totals,
            "actor": "script:import_license_inventory",
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        return {**output, **totals}
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=private_input_path)
    parser.add_argument("--apply", action="store_true", help="Persist encrypted keys; default is dry-run")
    args = parser.parse_args()
    result = asyncio.run(run(args.csv_path, args.apply))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
