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
        # Create test data - mix of default and non-default
        default_mcc = MCCCode(mcc_code=5411, name="Grocery Stores, Supermarkets", is_default=True)
        non_default_mcc = MCCCode(mcc_code=1234, name="Some Other Store", is_default=False)
        
        db.add(default_mcc)
        db.add(non_default_mcc)
        db.commit()
        
        # Mock authentication
        with patch('app.dependencies.get_current_user_id', return_value=1):
            response = client.get("/mcc/codes")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "language" in data
        assert data["total"] == 2
        assert data["language"] is None
        assert len(data["items"]) == 2
        
        # Check that both default and non-default codes are returned
        mcc_codes = [item["mcc_code"] for item in data["items"]]
        assert 5411 in mcc_codes
        assert 1234 in mcc_codes
        
        # Check default flag
        for item in data["items"]:
            if item["mcc_code"] == 5411:
                assert item["is_default"] is True
            elif item["mcc_code"] == 1234:
                assert item["is_default"] is False

    def test_get_all_mcc_codes_with_language(self, client: TestClient, db: Session):
        """Test getting all MCC codes with language parameter"""
        # Create test data
        default_mcc = MCCCode(mcc_code=5411, name="Grocery Stores, Supermarkets", is_default=True)
        non_default_mcc = MCCCode(mcc_code=1234, name="Some Other Store", is_default=False)
        
        db.add(default_mcc)
        db.add(non_default_mcc)
        db.flush()  # Get the IDs
        
        # Add translations
        translation1 = MCCTranslation(
            mcc_code=5411, 
            lang="ru", 
            text="Продуктовые магазины, супермаркеты"
        )
        translation2 = MCCTranslation(
            mcc_code=1234, 
            lang="ru", 
            text="Какой-то другой магазин"
        )
        
        db.add(translation1)
        db.add(translation2)
        db.commit()
        
        # Mock authentication
        with patch('app.dependencies.get_current_user_id', return_value=1):
            response = client.get("/categories/mcc-codes?language=ru")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["language"] == "ru"
        assert len(data["items"]) == 2
        
        # Check translations
        for item in data["items"]:
            if item["mcc_code"] == 5411:
                assert item["translation"] == "Продуктовые магазины, супермаркеты"
            elif item["mcc_code"] == 1234:
                assert item["translation"] == "Какой-то другой магазин"

    def test_get_all_mcc_codes_with_language_no_translation(self, client: TestClient, db: Session):
        """Test getting all MCC codes with language parameter but no translation available"""
        # Create test data
        mcc_code = MCCCode(mcc_code=5411, name="Grocery Stores, Supermarkets", is_default=True)
        db.add(mcc_code)
        db.commit()
        
        # Mock authentication
        with patch('app.dependencies.get_current_user_id', return_value=1):
            response = client.get("/categories/mcc-codes?language=uk")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["language"] == "uk"
        assert len(data["items"]) == 1
        assert data["items"][0]["mcc_code"] == 5411
        assert data["items"][0]["name"] == "Grocery Stores, Supermarkets"
        assert data["items"][0]["translation"] is None  # No translation available
        assert data["items"][0]["is_default"] is True

    def test_get_all_mcc_codes_ukrainian_language(self, client: TestClient, db: Session):
        """Test getting all MCC codes with Ukrainian translations"""
        # Create test data
        mcc_code = MCCCode(mcc_code=5411, name="Grocery Stores, Supermarkets", is_default=True)
        db.add(mcc_code)
        db.flush()  # Get the ID
        
        translation = MCCTranslation(
            mcc_code=5411, 
            lang="uk", 
            text="Продуктові магазини, супермаркети"
        )
        db.add(translation)
        db.commit()
        
        # Mock authentication
        with patch('app.dependencies.get_current_user_id', return_value=1):
            response = client.get("/categories/mcc-codes?language=uk")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["language"] == "uk"
        assert len(data["items"]) == 1
        assert data["items"][0]["mcc_code"] == 5411
        assert data["items"][0]["name"] == "Grocery Stores, Supermarkets"
        assert data["items"][0]["translation"] == "Продуктові магазини, супермаркети"
        assert data["items"][0]["is_default"] is True

    def test_get_all_mcc_codes_english_language(self, client: TestClient, db: Session):
        """Test getting all MCC codes with English language (should return English names)"""
        # Create test data
        mcc_code = MCCCode(mcc_code=5411, name="Grocery Stores, Supermarkets", is_default=True)
        db.add(mcc_code)
        db.commit()
        
        # Mock authentication
        with patch('app.dependencies.get_current_user_id', return_value=1):
            response = client.get("/categories/mcc-codes?language=en")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["language"] == "en"
        assert len(data["items"]) == 1
        assert data["items"][0]["mcc_code"] == 5411
        assert data["items"][0]["name"] == "Grocery Stores, Supermarkets"
        assert data["items"][0]["translation"] is None  # English is default, no translation needed
        assert data["items"][0]["is_default"] is True

    def test_get_all_mcc_codes_unsupported_language(self, client: TestClient, db: Session):
        """Test getting all MCC codes with unsupported language (should fallback to English)"""
        # Create test data
        mcc_code = MCCCode(mcc_code=5411, name="Grocery Stores, Supermarkets", is_default=True)
        db.add(mcc_code)
        db.commit()
        
        # Mock authentication
        with patch('app.dependencies.get_current_user_id', return_value=1):
            response = client.get("/categories/mcc-codes?language=fr")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["language"] == "fr"  # The parameter is still returned as requested
        assert len(data["items"]) == 1
        assert data["items"][0]["mcc_code"] == 5411
        assert data["items"][0]["name"] == "Grocery Stores, Supermarkets"
        assert data["items"][0]["translation"] is None  # Fallback to English
        assert data["items"][0]["is_default"] is True

    def test_get_all_mcc_codes_empty_result(self, client: TestClient, db: Session):
        """Test getting all MCC codes when none exist"""
        # Mock authentication
        with patch('app.dependencies.get_current_user_id', return_value=1):
            response = client.get("/mcc/codes")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["language"] is None

    def test_get_all_mcc_codes_unauthorized(self, client: TestClient):
        """Test that unauthorized requests are rejected"""
        response = client.get("/categories/mcc-codes")
        assert response.status_code == 401
