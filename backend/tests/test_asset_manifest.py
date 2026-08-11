from pathlib import Path

from PIL import Image

from asset_manifest import build_image_rights_manifest, build_provenance_manifest


def test_image_manifest_fingerprints_assets_but_keeps_rights_unverified(tmp_path: Path):
    image = tmp_path / "test.webp"
    Image.new("RGB", (640, 480), "white").save(image, "WEBP")
    products = [{"slug": "test", "image_url": "/products/test.webp", "sku": "LP-TEST"}]
    manifest, report = build_image_rights_manifest(products, tmp_path)
    record = manifest["test"]
    assert record["sha256"] and len(record["sha256"]) == 64
    assert (record["width"], record["height"]) == (640, 480)
    assert record["status"] == "unverified"
    assert record["rights_basis"] is None
    assert report == {"products": 1, "assets_found": 1, "assets_missing": 0, "orphan_assets": 0, "below_500": 1, "approved": 0}


def test_provenance_manifest_never_invents_supplier_evidence():
    manifest = build_provenance_manifest([{"slug": "test", "sku": "LP-TEST"}])
    assert manifest["test"] == {
        "sku": "LP-TEST",
        "status": "unverified",
        "supplier_name": None,
        "source_type": None,
        "evidence_refs": [],
        "reviewed_by": None,
        "reviewed_at": None,
    }
