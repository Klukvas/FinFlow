"""
Tests for app/dependencies.py - dependency functions.
Covers: verify_internal_token, decode_token, get_current_user_id,
        get_workspace_id, get_db.
"""
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from unittest.mock import patch, MagicMock
from jose import jwt

from app.dependencies import (
    verify_internal_token,
    decode_token,
    get_current_user_id,
    get_workspace_id,
)
from app.config import settings
from app.tests.conftest import TEST_WORKSPACE_ID_HEADER


# ---------------------------------------------------------------------------
# decode_token
# ---------------------------------------------------------------------------

class TestDecodeToken:
    def test_valid_token_returns_user_id(self):
        user_id = 42
        token = jwt.encode(
            {"sub": str(user_id)}, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        result = decode_token(token)
        assert result == user_id

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_token("not.a.valid.token")
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_missing_sub_raises_401(self):
        token = jwt.encode({"user": "noid"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_non_integer_sub_raises_401(self):
        token = jwt.encode(
            {"sub": "not-an-integer"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_raises_401(self):
        import time
        token = jwt.encode(
            {"sub": "1", "exp": int(time.time()) - 10},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# verify_internal_token
# ---------------------------------------------------------------------------

class TestVerifyInternalToken:
    def _make_request(self, headers=None):
        mock_request = MagicMock()
        mock_request.headers = headers or {}
        return mock_request

    def test_valid_token_does_not_raise(self):
        request = self._make_request({"X-Internal-Token": settings.INTERNAL_SECRET_TOKEN})
        # Should not raise
        verify_internal_token(request)

    def test_missing_token_raises_403(self):
        request = self._make_request({})
        with pytest.raises(HTTPException) as exc_info:
            verify_internal_token(request)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_token_raises_403(self):
        request = self._make_request({"X-Internal-Token": "wrong-token"})
        with pytest.raises(HTTPException) as exc_info:
            verify_internal_token(request)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# get_current_user_id
# ---------------------------------------------------------------------------

class TestGetCurrentUserId:
    """Tests for get_current_user_id using HTTPAuthorizationCredentials (shared auth)."""

    def _make_credentials(self, token: str) -> HTTPAuthorizationCredentials:
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    def test_valid_bearer_token_returns_user_id(self):
        user_id = 99
        token = jwt.encode(
            {"sub": str(user_id)}, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        credentials = self._make_credentials(token)
        result = get_current_user_id(credentials)
        assert result == user_id

    def test_invalid_bearer_token_raises_401(self):
        credentials = self._make_credentials("bad.token.here")
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(credentials)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_token_raises_401(self):
        credentials = self._make_credentials("")
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(credentials)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# get_workspace_id
# ---------------------------------------------------------------------------

class TestGetWorkspaceId:
    def test_valid_uuid_header_returns_uuid(self):
        result = get_workspace_id(x_workspace_id=TEST_WORKSPACE_ID_HEADER)
        from uuid import UUID
        assert isinstance(result, UUID)
        assert str(result) == TEST_WORKSPACE_ID_HEADER

    def test_missing_header_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            get_workspace_id(x_workspace_id=None)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "X-Workspace-Id" in exc_info.value.detail

    def test_invalid_uuid_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            get_workspace_id(x_workspace_id="not-a-uuid")
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid workspace ID format" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Via HTTP client - edge cases
# ---------------------------------------------------------------------------

class TestAuthViaHTTP:
    def test_missing_authorization_header_returns_403_via_http(self, client):
        """Verify that missing auth header returns 403 via HTTP (HTTPBearer)."""
        response = client.get(
            "/categories/",
            headers={"X-Workspace-Id": TEST_WORKSPACE_ID_HEADER},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_token_format_returns_403_via_http(self, client):
        """Verify that an invalid token format returns 403 via HTTP (HTTPBearer)."""
        response = client.get(
            "/categories/",
            headers={
                "Authorization": "Basic invalidformat",
                "X-Workspace-Id": TEST_WORKSPACE_ID_HEADER,
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
