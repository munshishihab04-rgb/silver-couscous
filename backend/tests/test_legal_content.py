from legal_content import LEGAL_PAGES
import db_migration


def test_default_public_settings_are_truthful_for_staging():
    settings = db_migration.DEFAULT_SETTINGS
    public_copy = f"{settings['site_title']} {settings['site_description']}".lower()
    assert "original" not in public_copy
    assert "verificat" not in public_copy
    assert settings["primary_email"] == "supporto@licenzpol.it"
    assert settings["demo_banner"] is True


def test_db_migration_uses_reviewed_legal_pages():
    assert db_migration.LEGAL_PAGES is LEGAL_PAGES


def test_legal_pages_are_complete_and_not_placeholders():
    required = {"privacy", "terms", "cookies", "withdrawal", "refunds", "delivery", "transparency"}
    assert required <= set(LEGAL_PAGES)
    for slug in required:
        page = LEGAL_PAGES[slug]
        text = f"{page['content_it']} {page['content_en']}".lower()
        assert "placeholder" not in text
        assert "segnaposto" not in text
        assert len(page["content_it"]) > 300


def test_legal_pages_identify_the_merchant():
    combined = " ".join(page["content_it"] for page in LEGAL_PAGES.values())
    assert "DIGITALSOFT DI MUNSHI SHIHAB" in combined
    assert "04358941203" in combined
    assert "supporto@licenzpol.it" in combined
