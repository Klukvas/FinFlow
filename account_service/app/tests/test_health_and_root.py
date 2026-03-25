"""
Tests for health check and root endpoints in app/main.py.
"""
import pytest
from fastapi.testclient import TestClient
from starlette import status


class TestHealthCheck:
    def test_health_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "account-service"


class TestRoot:
    def test_root_returns_200(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Account Service API"
        assert "version" in data
