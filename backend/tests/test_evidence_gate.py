from evidence import (
    bind_image_fingerprint,
    image_rights_evidence_verified,
    provenance_evidence_verified,
)
from merchant_admin import evidence_update_blockers


def complete_provenance_evidence():
    return {
        "supplier_name": "Verified Supplier S.r.l.",
        "source_type": "authorized_distributor",
        "evidence_refs": ["private://documents/supplier-agreement-2026"],
        "reviewed_by": "admin@licenzpol.it",
        "reviewed_at": "2026-08-11T00:00:00+00:00",
    }


def complete_image_evidence():
    return {
        "asset_path": "/products/test.webp",
        "sha256": "a" * 64,
        "width": 1000,
        "height": 1000,
        "rights_basis": "manufacturer_authorized",
        "evidence_refs": ["private://documents/image-authorization-2026"],
        "reviewed_by": "admin@licenzpol.it",
        "reviewed_at": "2026-08-11T00:00:00+00:00",
    }


def test_provenance_requires_documented_supplier_and_review():
    assert provenance_evidence_verified(complete_provenance_evidence()) is True
    incomplete = complete_provenance_evidence()
    incomplete["evidence_refs"] = []
    assert provenance_evidence_verified(incomplete) is False


def test_image_rights_require_asset_fingerprint_and_documented_basis():
    assert image_rights_evidence_verified(complete_image_evidence()) is True
    incomplete = complete_image_evidence()
    incomplete["rights_basis"] = "unknown"
    assert image_rights_evidence_verified(incomplete) is False


def test_admin_cannot_mark_evidence_verified_with_flags_only():
    existing = {"provenance_evidence_private": {}, "image_rights_evidence_private": {}}
    blockers = evidence_update_blockers(existing, {
        "provenance_status": "verified",
        "image_rights_approved": True,
    })
    assert blockers == ["provenance_evidence_invalid", "image_rights_evidence_invalid"]


def test_admin_can_mark_evidence_only_with_complete_private_records():
    existing = {}
    update = {
        "provenance_status": "verified",
        "provenance_evidence_private": complete_provenance_evidence(),
        "image_rights_approved": True,
        "image_rights_evidence_private": complete_image_evidence(),
    }
    assert evidence_update_blockers(existing, update) == []


def test_submitted_image_review_cannot_replace_server_fingerprint():
    existing = complete_image_evidence()
    submitted = {**existing, "sha256": "b" * 64, "width": 1, "height": 1, "rights_basis": "owned"}
    bound = bind_image_fingerprint(existing, submitted)
    assert bound["sha256"] == "a" * 64
    assert (bound["width"], bound["height"]) == (1000, 1000)
    assert bound["rights_basis"] == "owned"
