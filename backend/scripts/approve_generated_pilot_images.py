#!/usr/bin/env python3
"""Approve only pilot images whose current hashes match the source-free generation receipt."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
MANIFEST_PATH = BACKEND / "data" / "image_rights_manifest.json"
RECEIPT_PATH = BACKEND / "data" / "pilot_image_generation_receipt.json"
PRIVATE_RECEIPT = ROOT / ".runtime" / "evidence" / "documents" / "pilot-image-generation-2026-08-11.json"


def main() -> None:
    if not PRIVATE_RECEIPT.exists():
        raise SystemExit("Private generation receipt missing")
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    if receipt.get("source_assets") != [] or receipt.get("vendor_logos_used") is not False:
        raise SystemExit("Receipt is not source-free")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    reviewed_at = datetime.now(timezone.utc).isoformat()
    approved = 0
    for item in receipt["items"]:
        slug = item["slug"]
        asset = ROOT / "frontend" / "public" / item["asset_path"].lstrip("/")
        actual_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
        record = manifest.get(slug)
        if not record or actual_hash != item["sha256"] or record.get("sha256") != actual_hash:
            raise SystemExit(f"Fingerprint mismatch for {slug}")
        record.update({
            "status": "approved",
            "rights_basis": "owned",
            "evidence_refs": ["private://documents/pilot-image-generation-2026-08-11"],
            "reviewed_by": "automation:hermes-agent",
            "reviewed_at": reviewed_at,
        })
        approved += 1
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"approved_generated_images": approved, "rights_basis": "owned"}))


if __name__ == "__main__":
    main()
