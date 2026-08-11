"""Validation for private provenance and image-rights evidence records."""
from __future__ import annotations

import re
from datetime import datetime

PROVENANCE_SOURCE_TYPES = {
    "manufacturer",
    "authorized_distributor",
    "documented_reseller",
}
IMAGE_RIGHTS_BASES = {
    "owned",
    "licensed",
    "manufacturer_authorized",
    "public_domain",
}
_PRIVATE_REF_PREFIX = "private://documents/"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _valid_refs(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(ref, str) and ref.startswith(_PRIVATE_REF_PREFIX) and len(ref) > len(_PRIVATE_REF_PREFIX)
        for ref in value
    )


def _valid_review(record: dict) -> bool:
    if not record.get("reviewed_by") or not record.get("reviewed_at"):
        return False
    try:
        datetime.fromisoformat(str(record["reviewed_at"]).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def provenance_evidence_verified(record: object) -> bool:
    if not isinstance(record, dict):
        return False
    return bool(
        record.get("supplier_name")
        and record.get("source_type") in PROVENANCE_SOURCE_TYPES
        and _valid_refs(record.get("evidence_refs"))
        and _valid_review(record)
    )


def bind_image_fingerprint(existing: object, submitted: object) -> dict:
    current = existing if isinstance(existing, dict) else {}
    review = submitted if isinstance(submitted, dict) else {}
    bound = dict(review)
    for key in ("asset_path", "sha256", "width", "height"):
        bound[key] = current.get(key)
    return bound


def image_rights_evidence_verified(record: object) -> bool:
    if not isinstance(record, dict):
        return False
    sha = str(record.get("sha256") or "").lower()
    return bool(
        str(record.get("asset_path") or "").startswith("/products/")
        and _SHA256.fullmatch(sha)
        and isinstance(record.get("width"), int) and record["width"] > 0
        and isinstance(record.get("height"), int) and record["height"] > 0
        and record.get("rights_basis") in IMAGE_RIGHTS_BASES
        and _valid_refs(record.get("evidence_refs"))
        and _valid_review(record)
    )
