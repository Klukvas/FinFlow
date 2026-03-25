"""
Tests for non-parse router endpoints and app-level routes.

Covers:
- GET /pdf/supported-banks
- GET /pdf/languages/{bank_name}
- GET /pdf/health
- GET /health (app root)
- GET / (root)
"""

import pytest
from fastapi.testclient import TestClient
from starlette import status


class TestSupportedBanks:
    """Tests for GET /pdf/supported-banks."""

    def test_returns_list_of_banks(self, client: TestClient):
        response = client.get("/pdf/supported-banks")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "supported_banks" in data
        assert "total_count" in data
        assert isinstance(data["supported_banks"], list)
        assert data["total_count"] > 0

    def test_all_banks_lowercase(self, client: TestClient):
        response = client.get("/pdf/supported-banks")
        data = response.json()
        for bank in data["supported_banks"]:
            assert bank == bank.lower()

    def test_contains_known_banks(self, client: TestClient):
        response = client.get("/pdf/supported-banks")
        banks = response.json()["supported_banks"]
        assert "monobank" in banks
        assert "privatbank" in banks

    def test_total_count_matches_list_length(self, client: TestClient):
        response = client.get("/pdf/supported-banks")
        data = response.json()
        assert data["total_count"] == len(data["supported_banks"])


class TestAvailableLanguages:
    """Tests for GET /pdf/languages/{bank_name}."""

    def test_get_languages_for_monobank(self, client: TestClient):
        response = client.get("/pdf/languages/monobank")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["bank"] == "MONOBANK"
        assert "available_languages" in data
        assert "ua" in data["available_languages"]

    def test_get_languages_case_insensitive(self, client: TestClient):
        response = client.get("/pdf/languages/MONOBANK")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["bank"] == "MONOBANK"

    def test_get_languages_for_privatbank(self, client: TestClient):
        response = client.get("/pdf/languages/privatbank")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["bank"] == "PRIVATBANK"

    def test_get_languages_total_count(self, client: TestClient):
        response = client.get("/pdf/languages/monobank")
        data = response.json()
        assert data["total_languages"] == len(data["available_languages"])

    def test_get_languages_unsupported_bank_returns_404(
        self, client: TestClient
    ):
        response = client.get("/pdf/languages/nonexistent_bank")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_languages_deel_only_english(self, client: TestClient):
        response = client.get("/pdf/languages/deel")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["available_languages"] == ["en"]


class TestPdfHealthCheck:
    """Tests for GET /pdf/health."""

    def test_returns_healthy(self, client: TestClient):
        response = client.get("/pdf/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pdf-parser"
        assert "supported_banks" in data
        assert data["supported_banks"] > 0


class TestAppHealthAndRoot:
    """Tests for app-level health and root endpoints."""

    def test_app_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pdf-parser-service"

    def test_root_endpoint(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "PDF Parser Service" in data["message"]
        assert "version" in data
