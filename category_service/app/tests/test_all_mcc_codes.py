import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.models.mcc import MCCCode, MCCTranslation
from app.schemas.category import DefaultCategoryOut


class TestAllMCCCodes:
    """Test cases for all MCC codes endpoint"""

    def test_get_all_mcc_codes_without_language(self, client: TestClient, db: Session):
        """Test getting all MCC codes without language parameter"""
        # Use unique MCC codes to avoid conflicts with other tests
        default_mcc = MCCCode(mcc_code=7001, name="Test Store Default", is_default=True)
        non_default_mcc = MCCCode(mcc_code=7002, name="Test Store Non-Default", is_default=False)

        db.add(default_mcc)
        db.add(non_default_mcc)
        db.commit()

        with patch("shared.auth.dependencies.decode_token", return_value=1):
            response = client.get(
                "/mcc/codes",
                headers={"Authorization": "Bearer testtoken"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "language" in data
        assert data["language"] is None

        mcc_codes = [item["mcc_code"] for item in data["items"]]
        assert 7001 in mcc_codes
        assert 7002 in mcc_codes

        for item in data["items"]:
            if item["mcc_code"] == 7001:
                assert item["is_default"] is True
            elif item["mcc_code"] == 7002:
                assert item["is_default"] is False

    def test_get_all_mcc_codes_with_language(self, client: TestClient, db: Session):
        """Test getting all MCC codes with language parameter"""
        default_mcc = MCCCode(mcc_code=7003, name="Test Grocery", is_default=True)
        non_default_mcc = MCCCode(mcc_code=7004, name="Test Other Store", is_default=False)

        db.add(default_mcc)
        db.add(non_default_mcc)
        db.flush()

        translation1 = MCCTranslation(
            mcc_code=7003,
            lang="ru",
            text="Тестовый продуктовый магазин"
        )
        translation2 = MCCTranslation(
            mcc_code=7004,
            lang="ru",
            text="Тестовый другой магазин"
        )

        db.add(translation1)
        db.add(translation2)
        db.commit()

        with patch("shared.auth.dependencies.decode_token", return_value=1):
            response = client.get(
                "/mcc/codes?language=ru",
                headers={"Authorization": "Bearer testtoken"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "ru"

        for item in data["items"]:
            if item["mcc_code"] == 7003:
                assert item["translation"] == "Тестовый продуктовый магазин"
            elif item["mcc_code"] == 7004:
                assert item["translation"] == "Тестовый другой магазин"

    def test_get_all_mcc_codes_with_language_no_translation(
        self, client: TestClient, db: Session
    ):
        """Test getting all MCC codes with language parameter but no translation available"""
        mcc_code = MCCCode(mcc_code=7005, name="Test Store No Translation", is_default=True)
        db.add(mcc_code)
        db.commit()

        with patch("shared.auth.dependencies.decode_token", return_value=1):
            response = client.get(
                "/mcc/codes?language=uk",
                headers={"Authorization": "Bearer testtoken"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "uk"

        # Find our inserted item
        item = next((i for i in data["items"] if i["mcc_code"] == 7005), None)
        assert item is not None
        assert item["name"] == "Test Store No Translation"
        assert item["translation"] is None
        assert item["is_default"] is True

    def test_get_all_mcc_codes_ukrainian_language(self, client: TestClient, db: Session):
        """Test getting all MCC codes with Ukrainian translations"""
        mcc_code = MCCCode(mcc_code=7006, name="Test Grocery UK", is_default=True)
        db.add(mcc_code)
        db.flush()

        translation = MCCTranslation(
            mcc_code=7006,
            lang="uk",
            text="Тестові продуктові магазини"
        )
        db.add(translation)
        db.commit()

        with patch("shared.auth.dependencies.decode_token", return_value=1):
            response = client.get(
                "/mcc/codes?language=uk",
                headers={"Authorization": "Bearer testtoken"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "uk"

        item = next((i for i in data["items"] if i["mcc_code"] == 7006), None)
        assert item is not None
        assert item["name"] == "Test Grocery UK"
        assert item["translation"] == "Тестові продуктові магазини"
        assert item["is_default"] is True

    def test_get_all_mcc_codes_english_language(self, client: TestClient, db: Session):
        """Test getting all MCC codes with English language (should return English names)"""
        mcc_code = MCCCode(mcc_code=7007, name="Test Grocery EN", is_default=True)
        db.add(mcc_code)
        db.commit()

        with patch("shared.auth.dependencies.decode_token", return_value=1):
            response = client.get(
                "/mcc/codes?language=en",
                headers={"Authorization": "Bearer testtoken"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"

        item = next((i for i in data["items"] if i["mcc_code"] == 7007), None)
        assert item is not None
        assert item["name"] == "Test Grocery EN"
        # The service returns the English name as translation when language="en"
        assert item["translation"] == "Test Grocery EN"
        assert item["is_default"] is True

    def test_get_all_mcc_codes_unsupported_language(self, client: TestClient, db: Session):
        """Test getting all MCC codes with unsupported language returns 422"""
        mcc_code = MCCCode(mcc_code=7008, name="Test Grocery FR", is_default=True)
        db.add(mcc_code)
        db.commit()

        with patch("shared.auth.dependencies.decode_token", return_value=1):
            response = client.get(
                "/mcc/codes?language=fr",
                headers={"Authorization": "Bearer testtoken"},
            )

        # 'fr' is not in SupportedLanguage enum.
        # The custom validation exception handler converts 422 to 400.
        assert response.status_code in (400, 422)

    def test_get_all_mcc_codes_empty_result(self, client: TestClient, db: Session):
        """Test getting all MCC codes - results may already contain entries from other tests"""
        with patch("shared.auth.dependencies.decode_token", return_value=1):
            response = client.get(
                "/mcc/codes",
                headers={"Authorization": "Bearer testtoken"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert "language" in data
        assert data["language"] is None

    def test_get_all_mcc_codes_unauthorized(self, client: TestClient):
        """Test that unauthorized requests are rejected"""
        response = client.get("/mcc/codes")
        assert response.status_code == 403
