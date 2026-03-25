"""
Unit tests for health check and root endpoints.

Tests cover:
- GET /health - Health check
- GET / - Root endpoint
"""
import pytest


class TestHealthEndpoint:
    """Tests for GET /health"""

    def test_health_check(self, client):
        """Health check returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "debt-service"
        assert "version" in data

    def test_health_check_version(self, client):
        """Health check returns correct version."""
        response = client.get("/health")

        assert response.json()["version"] == "2.0.0"


class TestRootEndpoint:
    """Tests for GET /"""

    def test_root(self, client):
        """Root endpoint returns service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Debt Service API"
        assert "version" in data
        assert data["docs"] == "/docs"
