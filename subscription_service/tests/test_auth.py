"""Tests for authentication utilities (verify_internal_token, verify_admin_token)."""

from __future__ import annotations

import time
import pytest
import jwt as pyjwt
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.utils.auth import verify_internal_token
from app.utils.admin_guard import verify_admin_token
from app.utils.errors import AuthError


# ======================================================================
# verify_internal_token
# ======================================================================


class TestVerifyInternalToken:
    """Tests for verify_internal_token."""

    def test_valid_token_passes(self):
        """Must not raise when token matches."""
        with patch("app.utils.auth.settings") as mock_settings:
            mock_settings.internal_secret_token = "my-secret"
            # Should not raise
            verify_internal_token(internal_token="my-secret")

    def test_invalid_token_raises_auth_error(self):
        """Must raise AuthError for wrong token."""
        with patch("app.utils.auth.settings") as mock_settings:
            mock_settings.internal_secret_token = "my-secret"
            with pytest.raises(AuthError, match="Invalid internal token"):
                verify_internal_token(internal_token="wrong-secret")

    def test_empty_configured_token_raises_auth_error(self):
        """Must raise AuthError when internal token is not configured."""
        with patch("app.utils.auth.settings") as mock_settings:
            mock_settings.internal_secret_token = ""
            with pytest.raises(AuthError, match="not configured"):
                verify_internal_token(internal_token="any-token")


# ======================================================================
# verify_admin_token
# ======================================================================


class TestVerifyAdminToken:
    """Tests for verify_admin_token."""

    JWT_SECRET = "test-jwt-secret"
    JWT_ALGORITHM = "HS256"

    def _make_token(self, role: str = "admin", exp_offset: int = 3600, sub: str = "admin_user") -> str:
        payload = {
            "sub": sub,
            "role": role,
            "exp": int(time.time()) + exp_offset,
        }
        return pyjwt.encode(payload, self.JWT_SECRET, algorithm=self.JWT_ALGORITHM)

    def _make_request(self, token: str | None = None, auth_header: str | None = None) -> MagicMock:
        request = MagicMock()
        if auth_header is not None:
            request.headers.get.return_value = auth_header
        elif token is not None:
            request.headers.get.return_value = f"Bearer {token}"
        else:
            request.headers.get.return_value = None
        return request

    def test_valid_admin_token(self):
        """Must return decoded payload for valid admin JWT."""
        token = self._make_token(role="admin")
        request = self._make_request(token=token)

        with patch("app.utils.admin_guard.settings") as mock_settings:
            mock_settings.jwt_secret_key = self.JWT_SECRET
            mock_settings.jwt_algorithm = self.JWT_ALGORITHM

            result = verify_admin_token(request)

        assert result["role"] == "admin"
        assert result["sub"] == "admin_user"

    def test_non_admin_role_raises_403(self):
        """Must raise 403 for non-admin users."""
        token = self._make_token(role="user")
        request = self._make_request(token=token)

        with patch("app.utils.admin_guard.settings") as mock_settings:
            mock_settings.jwt_secret_key = self.JWT_SECRET
            mock_settings.jwt_algorithm = self.JWT_ALGORITHM

            with pytest.raises(HTTPException) as exc_info:
                verify_admin_token(request)
            assert exc_info.value.status_code == 403

    def test_missing_auth_header_raises_401(self):
        """Must raise 401 when Authorization header is missing."""
        request = self._make_request()

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(request)
        assert exc_info.value.status_code == 401

    def test_invalid_token_format_raises_401(self):
        """Must raise 401 for non-Bearer tokens."""
        request = self._make_request(auth_header="Token some-value")

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(request)
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        """Must raise 401 for expired JWTs."""
        token = self._make_token(exp_offset=-3600)  # Already expired
        request = self._make_request(token=token)

        with patch("app.utils.admin_guard.settings") as mock_settings:
            mock_settings.jwt_secret_key = self.JWT_SECRET
            mock_settings.jwt_algorithm = self.JWT_ALGORITHM

            with pytest.raises(HTTPException) as exc_info:
                verify_admin_token(request)
            assert exc_info.value.status_code == 401

    def test_invalid_jwt_raises_401(self):
        """Must raise 401 for malformed JWTs."""
        request = self._make_request(token="not.a.valid.jwt")

        with patch("app.utils.admin_guard.settings") as mock_settings:
            mock_settings.jwt_secret_key = self.JWT_SECRET
            mock_settings.jwt_algorithm = self.JWT_ALGORITHM

            with pytest.raises(HTTPException) as exc_info:
                verify_admin_token(request)
            assert exc_info.value.status_code == 401

    def test_jwt_secret_not_configured_raises_500(self):
        """Must raise 500 when JWT secret is not configured."""
        token = self._make_token()
        request = self._make_request(token=token)

        with patch("app.utils.admin_guard.settings") as mock_settings:
            mock_settings.jwt_secret_key = ""

            with pytest.raises(HTTPException) as exc_info:
                verify_admin_token(request)
            assert exc_info.value.status_code == 500
