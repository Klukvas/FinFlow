"""Tests for admin_guard utility (JWT admin authorization)."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

import jwt as pyjwt

from app.utils.admin_guard import verify_admin_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

JWT_SECRET = "test-jwt-secret"
JWT_ALGORITHM = "HS256"


def _make_request(auth_header: str | None = None) -> MagicMock:
    """Build a fake Request with optional Authorization header."""
    request = MagicMock()
    headers = {}
    if auth_header is not None:
        headers["Authorization"] = auth_header
    request.headers = headers
    return request


def _encode_token(payload: dict, secret: str = JWT_SECRET) -> str:
    """Create a valid JWT token."""
    return pyjwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestVerifyAdminToken:
    """Tests for verify_admin_token dependency."""

    @patch("app.utils.admin_guard.settings")
    def test_valid_admin_token_returns_payload(self, mock_settings):
        """Must return decoded payload for a valid admin JWT."""
        mock_settings.jwt_secret_key = JWT_SECRET
        mock_settings.jwt_algorithm = JWT_ALGORITHM

        payload = {"sub": "admin_user", "role": "admin", "exp": datetime.utcnow() + timedelta(hours=1)}
        token = _encode_token(payload)
        request = _make_request(f"Bearer {token}")

        result = verify_admin_token(request)

        assert result["sub"] == "admin_user"
        assert result["role"] == "admin"

    @patch("app.utils.admin_guard.settings")
    def test_missing_authorization_header_raises_401(self, mock_settings):
        """Must raise 401 when Authorization header is missing."""
        mock_settings.jwt_secret_key = JWT_SECRET
        request = _make_request(auth_header=None)

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(request)

        assert exc_info.value.status_code == 401
        assert "Authorization header required" in exc_info.value.detail

    @patch("app.utils.admin_guard.settings")
    def test_invalid_token_format_raises_401(self, mock_settings):
        """Must raise 401 when token does not start with 'Bearer '."""
        mock_settings.jwt_secret_key = JWT_SECRET
        request = _make_request("Basic some-token")

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(request)

        assert exc_info.value.status_code == 401
        assert "Invalid token format" in exc_info.value.detail

    @patch("app.utils.admin_guard.settings")
    def test_jwt_secret_not_configured_raises_500(self, mock_settings):
        """Must raise 500 when jwt_secret_key is empty."""
        mock_settings.jwt_secret_key = ""
        request = _make_request("Bearer some-token")

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(request)

        assert exc_info.value.status_code == 500
        assert "Service configuration error" in exc_info.value.detail

    @patch("app.utils.admin_guard.settings")
    def test_non_admin_role_raises_403(self, mock_settings):
        """Must raise 403 when user role is not 'admin'."""
        mock_settings.jwt_secret_key = JWT_SECRET
        mock_settings.jwt_algorithm = JWT_ALGORITHM

        payload = {"sub": "regular_user", "role": "user", "exp": datetime.utcnow() + timedelta(hours=1)}
        token = _encode_token(payload)
        request = _make_request(f"Bearer {token}")

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(request)

        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail

    @patch("app.utils.admin_guard.settings")
    def test_missing_role_claim_raises_403(self, mock_settings):
        """Must raise 403 when JWT has no 'role' claim."""
        mock_settings.jwt_secret_key = JWT_SECRET
        mock_settings.jwt_algorithm = JWT_ALGORITHM

        payload = {"sub": "user_no_role", "exp": datetime.utcnow() + timedelta(hours=1)}
        token = _encode_token(payload)
        request = _make_request(f"Bearer {token}")

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(request)

        assert exc_info.value.status_code == 403

    @patch("app.utils.admin_guard.settings")
    def test_expired_token_raises_401(self, mock_settings):
        """Must raise 401 for an expired JWT."""
        mock_settings.jwt_secret_key = JWT_SECRET
        mock_settings.jwt_algorithm = JWT_ALGORITHM

        payload = {"sub": "admin_user", "role": "admin", "exp": datetime.utcnow() - timedelta(hours=1)}
        token = _encode_token(payload)
        request = _make_request(f"Bearer {token}")

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(request)

        assert exc_info.value.status_code == 401
        assert "Token has expired" in exc_info.value.detail

    @patch("app.utils.admin_guard.settings")
    def test_invalid_token_raises_401(self, mock_settings):
        """Must raise 401 for a malformed/corrupt JWT."""
        mock_settings.jwt_secret_key = JWT_SECRET
        mock_settings.jwt_algorithm = JWT_ALGORITHM

        request = _make_request("Bearer not.a.valid.jwt")

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(request)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    @patch("app.utils.admin_guard.settings")
    def test_wrong_secret_raises_401(self, mock_settings):
        """Must raise 401 when token was signed with a different secret."""
        mock_settings.jwt_secret_key = JWT_SECRET
        mock_settings.jwt_algorithm = JWT_ALGORITHM

        payload = {"sub": "admin_user", "role": "admin", "exp": datetime.utcnow() + timedelta(hours=1)}
        token = _encode_token(payload, secret="wrong-secret")
        request = _make_request(f"Bearer {token}")

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(request)

        assert exc_info.value.status_code == 401
