"""Fail-closed pilot-catalog selection and non-inventory review gates."""
from __future__ import annotations

from evidence import image_rights_evidence_verified, provenance_evidence_verified


_ALLOWED_SOURCES = {"manufacturer", "authorized_distributor", "documented_reseller"}
_ALLOWED_IMAGE_RIGHTS = {"owned", "licensed", "manufacturer_authorized", "public_domain"}


def _private_ref(value: object) -> bool:
    return isinstance(value, str) and value.startswith("private://documents/") and len(value) > len("private://documents/")


def validate_review_row(row: dict) -> list[str]:
    blockers: list[str] = []
    try:
        if float(row.get("selling_price_eur_vat_included") or 0) <= 0:
            blockers.append("selling_price_missing")
    except (TypeError, ValueError):
        blockers.append("selling_price_missing")
    if not row.get("google_product_category"):
        blockers.append("google_category_missing")
    if row.get("identifier_type") not in {"gtin", "mpn"} or not row.get("verified_identifier"):
        blockers.append("verified_identifier_missing")
    if not _private_ref(row.get("identifier_evidence_ref")):
        blockers.append("identifier_evidence_ref_invalid")
    if not row.get("supplier_name"):
        blockers.append("supplier_name_missing")
    if row.get("provenance_source_type") not in _ALLOWED_SOURCES:
        blockers.append("provenance_source_type_invalid")
    if not _private_ref(row.get("provenance_evidence_ref")):
        blockers.append("provenance_evidence_ref_invalid")
    if row.get("image_rights_basis") not in _ALLOWED_IMAGE_RIGHTS:
        blockers.append("image_rights_basis_invalid")
    if not _private_ref(row.get("image_evidence_ref")):
        blockers.append("image_evidence_ref_invalid")
    if row.get("decision") != "approved":
        blockers.append("decision_not_approved")
    return blockers


def shortlist_blockers(product: dict) -> list[str]:
    blockers: list[str] = []
    for field in ("sku", "brand", "image_url"):
        if not product.get(field):
            blockers.append(f"{field}_missing")
    image = product.get("image_rights_evidence_private") or {}
    if not image.get("sha256"):
        blockers.append("image_fingerprint_missing")
    elif min(image.get("width") or 0, image.get("height") or 0) < 500:
        blockers.append("image_resolution_low")
    if product.get("gtin_status") in {"duplicate_conflict", "invalid_checksum"}:
        blockers.append("identifier_conflict")
    elif product.get("gtin_checksum_status") != "valid":
        blockers.append("candidate_gtin_not_formally_valid")
    return blockers


def catalog_review_blockers(product: dict) -> list[str]:
    blockers: list[str] = []
    for field in ("sku", "brand", "image_url", "condition"):
        if not product.get(field):
            blockers.append(f"{field}_missing")
    try:
        if float(product.get("selling_price_eur") or 0) <= 0:
            blockers.append("selling_price_missing")
    except (TypeError, ValueError):
        blockers.append("selling_price_missing")
    if not product.get("google_product_category"):
        blockers.append("google_category_missing")
    gtin_verified = bool(product.get("gtin")) and product.get("gtin_status") == "verified"
    mpn_verified = bool(product.get("mpn")) and product.get("mpn_status") == "verified"
    if not (gtin_verified or mpn_verified):
        blockers.append("identifier_assignment_unverified")
    if product.get("provenance_status") != "verified" or not provenance_evidence_verified(
        product.get("provenance_evidence_private")
    ):
        blockers.append("provenance_evidence_missing")
    if product.get("image_rights_approved") is not True or not image_rights_evidence_verified(
        product.get("image_rights_evidence_private")
    ):
        blockers.append("image_rights_evidence_missing")
    return blockers
