"""Generate auditable, fail-closed provenance and image-rights manifests."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image


def _asset_name(image_url: str | None) -> str | None:
    if not image_url:
        return None
    return Path(urlparse(image_url).path).name or None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_image_rights_manifest(products: list[dict], assets_dir: Path) -> tuple[dict, dict]:
    manifest: dict[str, dict] = {}
    referenced: set[str] = set()
    found = 0
    missing = 0
    below_500 = 0
    for product in products:
        slug = product["slug"]
        name = _asset_name(product.get("image_url"))
        path = assets_dir / name if name else None
        record = {
            "sku": product.get("sku"),
            "asset_path": f"/products/{name}" if name else None,
            "sha256": None,
            "width": None,
            "height": None,
            "status": "unverified",
            "rights_basis": None,
            "evidence_refs": [],
            "reviewed_by": None,
            "reviewed_at": None,
        }
        if path and path.is_file():
            referenced.add(name)
            with Image.open(path) as image:
                record["width"], record["height"] = image.size
            if min(record["width"], record["height"]) < 500:
                below_500 += 1
            record["sha256"] = _sha256(path)
            found += 1
        else:
            missing += 1
        manifest[slug] = record
    all_assets = {path.name for path in assets_dir.glob("*.webp")}
    report = {
        "products": len(products),
        "assets_found": found,
        "assets_missing": missing,
        "orphan_assets": len(all_assets - referenced),
        "below_500": below_500,
        "approved": 0,
    }
    return manifest, report


def build_provenance_manifest(products: list[dict]) -> dict:
    return {
        product["slug"]: {
            "sku": product.get("sku"),
            "status": "unverified",
            "supplier_name": None,
            "source_type": None,
            "evidence_refs": [],
            "reviewed_by": None,
            "reviewed_at": None,
        }
        for product in products
    }
