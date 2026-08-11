import pytest

from admin_routes import sanitize_product_editor_update


def test_general_product_editor_cannot_bypass_merchant_evidence_workflow():
    with pytest.raises(ValueError):
        sanitize_product_editor_update({
            "name": "Safe name",
            "merchant_approved": True,
            "provenance_status": "verified",
            "image_rights_approved": True,
        })


def test_general_product_editor_accepts_content_fields_only():
    update = sanitize_product_editor_update({"name": "Updated", "description_it": "Testo"})
    assert update == {"name": "Updated", "description_it": "Testo"}
