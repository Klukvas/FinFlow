"""Tests for income internal endpoints and dependencies"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException

from app.dependencies import verify_internal_token


class TestVerifyInternalToken:
    def test_missing_token_raises_403(self):
        """Verify 403 when X-Internal-Token header is missing"""
        request = MagicMock()
        request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            verify_internal_token(request)

        assert exc_info.value.status_code == 403
        assert "Internal token required" in exc_info.value.detail

    def test_invalid_token_raises_403(self):
        """Verify 403 when token doesn't match INTERNAL_SECRET_TOKEN"""
        request = MagicMock()
        request.headers = {"X-Internal-Token": "wrong-token"}

        with pytest.raises(HTTPException) as exc_info:
            verify_internal_token(request)

        assert exc_info.value.status_code == 403
        assert "Unauthorized internal access" in exc_info.value.detail

    def test_valid_token_passes(self):
        """Verify no exception when token matches settings"""
        from app.config import settings

        request = MagicMock()
        request.headers = {"X-Internal-Token": settings.INTERNAL_SECRET_TOKEN}

        # Should not raise
        verify_internal_token(request)

    def test_hardcoded_token_rejected(self):
        """Verify the old hardcoded 'my-secret-token' is NOT accepted"""
        request = MagicMock()
        request.headers = {"X-Internal-Token": "my-secret-token"}

        from app.config import settings
        if settings.INTERNAL_SECRET_TOKEN == "my-secret-token":
            pytest.skip("INTERNAL_SECRET_TOKEN happens to equal the old hardcoded value")

        with pytest.raises(HTTPException) as exc_info:
            verify_internal_token(request)

        assert exc_info.value.status_code == 403
