#!/usr/bin/env python3
"""Approve source-free artwork for the market-observed catalog."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
MANIFEST_PATH = BACKEND / "data" / "image_rights_manifest.json"
RECEIPT_PATH = BACKEND / "data" / "market_image_generation_receipt.json"
PRIVATE_RECEIPT = ROOT / ".runtime" / "evidence" / "documents" / "market-image-generation-2026-08-11.json"


def main() -> None:
    if not PRIVATE_RECEIPT.exists():
        raise SystemExit("Private generation receipt missing")
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    reviewed_at = datetime.now(timezone.utc).isoformat()
    for item in receipt["items"]:
        asset = ROOT / "frontend" / "public" / item["asset_path"].lstrip("/")
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
        record = manifest.get(item["slug"])
        if not record or digest != item["sha256"] or record.get("sha256") != digest:
            raise SystemExit(f"Fingerprint mismatch for {item['slug']}")
        record.update({
            "status": "approved",
            "rights_basis": "owned",
            "evidence_refs": ["private://documents/market-image-generation-2026-08-11"],
            "reviewed_by": "automation:hermes-agent",
            "reviewed_at": reviewed_at,
        })
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"approved_generated_images": len(receipt["items"]), "rights_basis": "owned"}))


if __name__ == "__main__":
    main()
