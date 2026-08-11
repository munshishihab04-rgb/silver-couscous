#!/usr/bin/env python3
"""Generate and safely refresh provenance/image evidence manifests."""
from __future__ import annotations

import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from asset_manifest import build_image_rights_manifest, build_provenance_manifest  # noqa: E402
from catalog import _load_csv  # noqa: E402
from evidence import image_rights_evidence_verified, provenance_evidence_verified  # noqa: E402

PROVENANCE_PATH = BACKEND / "data" / "provenance_manifest.json"
IMAGE_PATH = BACKEND / "data" / "image_rights_manifest.json"
AUDIT_PATH = BACKEND / "data" / "evidence_audit.json"
ASSETS = ROOT / "frontend" / "public" / "products"


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    products = _load_csv()
    provenance = build_provenance_manifest(products)
    images, image_report = build_image_rights_manifest(products, ASSETS)
    old_provenance = _load(PROVENANCE_PATH)
    old_images = _load(IMAGE_PATH)

    for slug, base in provenance.items():
        previous = old_provenance.get(slug)
        if previous:
            provenance[slug] = {**base, **previous, "sku": base["sku"]}

    for slug, base in images.items():
        previous = old_images.get(slug)
        if previous and previous.get("sha256") == base.get("sha256"):
            images[slug] = {
                **base,
                **{key: previous.get(key) for key in (
                    "status", "rights_basis", "evidence_refs", "reviewed_by", "reviewed_at"
                )},
                "sku": base["sku"],
                "asset_path": base["asset_path"],
                "sha256": base["sha256"],
                "width": base["width"],
                "height": base["height"],
            }

    provenance_verified = sum(provenance_evidence_verified(record) for record in provenance.values())
    images_approved = sum(image_rights_evidence_verified(record) for record in images.values())
    image_report["approved"] = images_approved
    audit = {
        "generated_at": "2026-08-11",
        "provenance": {
            "products": len(provenance),
            "verified": provenance_verified,
            "unverified": len(provenance) - provenance_verified,
        },
        "images": image_report,
        "policy": {
            "provenance": "No product is verified without private documentary references, supplier identity and reviewer metadata.",
            "images": "A file hash proves asset identity, not usage rights. Approval requires a documented rights basis and private evidence reference.",
        },
    }

    PROVENANCE_PATH.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    IMAGE_PATH.write_text(json.dumps(images, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit))


if __name__ == "__main__":
    main()
