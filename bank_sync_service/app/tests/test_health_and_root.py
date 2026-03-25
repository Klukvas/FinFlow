"""Tests for health check and root endpoints defined in app/main.py."""

from fastapi.testclient import TestClient
from fastapi import status


class TestHealthCheck:
    """Tests for GET /health"""

    def test_health_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_response_body(self, client: TestClient):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "bank-sync-service"
        assert "version" in data


class TestRoot:
    """Tests for GET /"""

    def test_root_returns_200(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK

    def test_root_response_body(self, client: TestClient):
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestExceptionHandlers:
    """Tests for custom exception handlers in main.py."""

    def test_validation_error_returns_422(self, client: TestClient):
        """Sending invalid data to a typed endpoint should return 422."""
        response = client.post(
            "/connections/",
            json={"token": ""},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "error" in data
        assert data["errorCode"] == "VALIDATION_ERROR"

    def test_validation_error_missing_required_field(self, client: TestClient):
        response = client.post(
            "/connections/",
            json={},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["errorCode"] == "VALIDATION_ERROR"
