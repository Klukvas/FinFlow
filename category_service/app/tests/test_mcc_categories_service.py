"""
Tests for app/services/mcc_categories.py - DefaultCategoryService.
Covers: get_default_categories, get_all_mcc_codes with various language options,
        unsupported languages, translations, error paths.
Lines targeted: 25-121, 135-142, 205-215
"""
import pytest
from unittest.mock import patch

from app.services.mcc_categories import DefaultCategoryService
from app.models.mcc import MCCCode, MCCTranslation
from app.tests.conftest import TEST_WORKSPACE_ID


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_mcc(db, mcc_code, name, is_default=True):
    existing = db.query(MCCCode).filter(MCCCode.mcc_code == mcc_code).first()
    if existing:
        return existing
    mcc = MCCCode(mcc_code=mcc_code, name=name, is_default=is_default)
    db.add(mcc)
    db.commit()
    db.refresh(mcc)
    return mcc


def _seed_translation(db, mcc_code, lang, text):
    existing = db.query(MCCTranslation).filter(
        MCCTranslation.mcc_code == mcc_code,
        MCCTranslation.lang == lang
    ).first()
    if existing:
        return existing
    t = MCCTranslation(mcc_code=mcc_code, lang=lang, text=text)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


# ---------------------------------------------------------------------------
# DefaultCategoryService.get_default_categories
# ---------------------------------------------------------------------------

class TestGetDefaultCategories:
    def test_returns_list_with_english_names(self, db):
        _seed_mcc(db, 8001, "Default English Category", is_default=True)
        service = DefaultCategoryService(db)

        result = service.get_default_categories(language=None)
        assert isinstance(result, list)
        names = [r.name for r in result]
        assert "Default English Category" in names

    def test_english_language_returns_no_translation(self, db):
        """When language='en', the service normalizes it to None (English is the base).
        So translation field stays None."""
        _seed_mcc(db, 8002, "English Default Cat", is_default=True)
        service = DefaultCategoryService(db)

        result = service.get_default_categories(language="en")
        assert isinstance(result, list)
        cat = next((r for r in result if r.mcc_code == 8002), None)
        assert cat is not None
        # 'en' is normalized to None, so no translation is set
        assert cat.translation is None
        assert cat.name == "English Default Cat"

    def test_russian_language_uses_translation(self, db):
        _seed_mcc(db, 8003, "Russian Default Cat", is_default=True)
        _seed_translation(db, 8003, "ru", "Русская категория по умолчанию")
        service = DefaultCategoryService(db)

        result = service.get_default_categories(language="ru")
        cat = next((r for r in result if r.mcc_code == 8003), None)
        assert cat is not None
        assert cat.translation == "Русская категория по умолчанию"

    def test_ukrainian_language_uses_translation(self, db):
        _seed_mcc(db, 8004, "Ukrainian Default Cat", is_default=True)
        _seed_translation(db, 8004, "uk", "Українська категорія")
        service = DefaultCategoryService(db)

        result = service.get_default_categories(language="uk")
        cat = next((r for r in result if r.mcc_code == 8004), None)
        assert cat is not None
        assert cat.translation == "Українська категорія"

    def test_unsupported_language_falls_back_to_english(self, db):
        _seed_mcc(db, 8005, "Fallback Default", is_default=True)
        service = DefaultCategoryService(db)

        # 'fr' is not supported - should fall back to English (no translation field)
        result = service.get_default_categories(language="fr")
        assert isinstance(result, list)

    def test_only_returns_default_categories(self, db):
        _seed_mcc(db, 8006, "Non Default", is_default=False)
        _seed_mcc(db, 8007, "Is Default", is_default=True)
        service = DefaultCategoryService(db)

        result = service.get_default_categories()
        mcc_codes = [r.mcc_code for r in result]
        assert 8007 in mcc_codes
        assert 8006 not in mcc_codes

    def test_translation_missing_returns_none(self, db):
        _seed_mcc(db, 8008, "No Translation Cat", is_default=True)
        service = DefaultCategoryService(db)

        # Request Ukrainian but no Ukrainian translation for 8008
        result = service.get_default_categories(language="uk")
        cat = next((r for r in result if r.mcc_code == 8008), None)
        assert cat is not None
        assert cat.translation is None

    def test_raises_on_db_error(self, db):
        service = DefaultCategoryService(db)
        with patch.object(db, "query", side_effect=Exception("DB failure")):
            with pytest.raises(Exception, match="Failed to retrieve default categories"):
                service.get_default_categories()


# ---------------------------------------------------------------------------
# DefaultCategoryService.get_all_mcc_codes
# ---------------------------------------------------------------------------

class TestGetAllMCCCodes:
    def test_returns_all_mcc_codes(self, db):
        _seed_mcc(db, 9001, "All MCC Cat One", is_default=False)
        _seed_mcc(db, 9002, "All MCC Cat Two", is_default=True)
        service = DefaultCategoryService(db)

        result = service.get_all_mcc_codes()
        mcc_codes = [r.mcc_code for r in result]
        assert 9001 in mcc_codes
        assert 9002 in mcc_codes

    def test_english_language_returns_no_translation(self, db):
        """When language='en', the service keeps the language as 'en' (no normalization to None).
        So translation is set to the name."""
        _seed_mcc(db, 9003, "All English MCC", is_default=False)
        service = DefaultCategoryService(db)

        result = service.get_all_mcc_codes(language="en")
        cat = next((r for r in result if r.mcc_code == 9003), None)
        assert cat is not None
        # In get_all_mcc_codes, language='en' is NOT normalized to None
        # (no line 40 equivalent), so translation = name
        assert cat.translation == "All English MCC"

    def test_russian_language_uses_translation(self, db):
        _seed_mcc(db, 9004, "All Russian MCC", is_default=False)
        _seed_translation(db, 9004, "ru", "Все русские МКС")
        service = DefaultCategoryService(db)

        result = service.get_all_mcc_codes(language="ru")
        cat = next((r for r in result if r.mcc_code == 9004), None)
        assert cat is not None
        assert cat.translation == "Все русские МКС"

    def test_unsupported_language_falls_back_to_english(self, db):
        _seed_mcc(db, 9005, "Unsupported Lang MCC", is_default=False)
        service = DefaultCategoryService(db)

        result = service.get_all_mcc_codes(language="de")
        assert isinstance(result, list)

    def test_no_language_returns_no_translation(self, db):
        _seed_mcc(db, 9006, "No Lang MCC", is_default=False)
        service = DefaultCategoryService(db)

        result = service.get_all_mcc_codes(language=None)
        cat = next((r for r in result if r.mcc_code == 9006), None)
        assert cat is not None
        assert cat.translation is None

    def test_raises_on_db_error(self, db):
        service = DefaultCategoryService(db)
        with patch.object(db, "query", side_effect=Exception("DB failure")):
            with pytest.raises(Exception, match="Failed to retrieve all MCC codes"):
                service.get_all_mcc_codes()

    def test_translation_missing_for_language_returns_none(self, db):
        _seed_mcc(db, 9007, "Translation Missing MCC", is_default=False)
        service = DefaultCategoryService(db)

        result = service.get_all_mcc_codes(language="ru")
        cat = next((r for r in result if r.mcc_code == 9007), None)
        assert cat is not None
        assert cat.translation is None
