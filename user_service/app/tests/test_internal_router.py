"""
Tests for the internal router endpoints.
Covers: app/routers/internal.py (50% -> target 80%+)
Lines: 14-21, 46-50, 75-81
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from app.main import app

client = TestClient(app)

INTERNAL_TOKEN = "test-internal-token"


def _register_user(email: str, password: str = "InternalPass1!") -> dict:
    """Register a user and return response JSON."""
    resp = client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _get_user_id(token: str) -> int:
    """Return the user ID for a given access token."""
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return me.json()["id"]


class TestInternalGetUserById:
    """Tests for GET /internal/users/{user_id}"""

    def test_missing_internal_token_returns_403(self):
        """Request without X-Internal-Token must be rejected."""
        response = client.get("/internal/users/1")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Unauthorized internal access" in response.json()["error"]

    def test_wrong_internal_token_returns_403(self):
        """Request with an incorrect token must be rejected."""
        response = client.get(
            "/internal/users/1",
            headers={"X-Internal-Token": "wrong-token"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Unauthorized internal access" in response.json()["error"]

    def test_get_existing_user_by_id(self):
        """Valid token + existing user returns user data."""
        resp_data = _register_user("internal_byid@example.com")
        token = resp_data["access_token"]
        user_id = _get_user_id(token)

        response = client.get(
            f"/internal/users/{user_id}",
            headers={"X-Internal-Token": INTERNAL_TOKEN},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "internal_byid@example.com"

    def test_get_nonexistent_user_returns_404(self):
        """Valid token + non-existent user ID returns 404."""
        response = client.get(
            "/internal/users/999999",
            headers={"X-Internal-Token": INTERNAL_TOKEN},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["error"].lower()


class TestInternalGetUserByEmail:
    """Tests for GET /internal/users/by-email/{email}"""

    def test_missing_internal_token_returns_403(self):
        """Request without X-Internal-Token must be rejected."""
        response = client.get("/internal/users/by-email/someone@example.com")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_wrong_internal_token_returns_403(self):
        """Wrong token is rejected."""
        response = client.get(
            "/internal/users/by-email/someone@example.com",
            headers={"X-Internal-Token": "bad-token"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_existing_user_by_email(self):
        """Valid token + existing email returns user data."""
        email = "internal_byemail@example.com"
        _register_user(email)

        response = client.get(
            f"/internal/users/by-email/{email}",
            headers={"X-Internal-Token": INTERNAL_TOKEN},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == email

    def test_get_nonexistent_email_returns_404(self):
        """Valid token + non-existent email returns 404."""
        response = client.get(
            "/internal/users/by-email/nobody@nowhere.com",
            headers={"X-Internal-Token": INTERNAL_TOKEN},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["error"].lower()

    def test_email_lookup_is_case_insensitive(self):
        """Email lookup normalises to lowercase."""
        email = "Internal_Case@Example.com"
        _register_user(email.lower())

        response = client.get(
            f"/internal/users/by-email/{email.lower()}",
            headers={"X-Internal-Token": INTERNAL_TOKEN},
        )
        assert response.status_code == status.HTTP_200_OK
