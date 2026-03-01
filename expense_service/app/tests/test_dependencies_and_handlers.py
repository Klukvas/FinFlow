"""
Tests for app/dependencies.py and app/exception_handlers.py.
Targets the remaining coverage gaps:
  - dependencies.py: 47% (decode_token, get_db, verify_internal_token, get_workspace_id)
  - exception_handlers.py: 72% (specific handler branches)
"""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from unittest.mock import MagicMock, patch, AsyncMock
from jose import jwt
from datetime import datetime, timedelta

from app.main import app
from app.dependencies import decode_token, get_workspace_id, verify_internal_token
from app.exceptions import (
    ErrorCode,
    ExpenseValidationError,
    ExpenseAmountError,
    ExpenseDateError,
    ExpenseDescriptionError,
    ExternalServiceError,
    ExpenseNotFoundError,
    StandardizedError,
)
from app.exception_handlers import (
    custom_validation_exception_handler,
    standardized_error_handler,
    expense_not_found_handler,
    expense_validation_handler,
    expense_amount_handler,
    expense_date_handler,
    expense_description_handler,
    external_service_handler,
    http_exception_handler,
)

SECRET_KEY = "test-secret-key"
ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# decode_token tests
# ---------------------------------------------------------------------------

class TestDecodeToken:
    def _make_token(self, payload: dict, key=SECRET_KEY) -> str:
        return jwt.encode(payload, key, algorithm=ALGORITHM)

    def test_valid_token_returns_user_id(self):
        token = self._make_token({"sub": "42", "exp": datetime.utcnow() + timedelta(hours=1)})
        result = decode_token(token)
        assert result == 42

    def test_expired_token_raises_401(self):
        token = self._make_token({"sub": "42", "exp": datetime.utcnow() - timedelta(hours=1)})
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401

    def test_invalid_signature_raises_401(self):
        token = self._make_token({"sub": "42"}, key="wrong-secret")
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401

    def test_missing_sub_raises_401(self):
        token = self._make_token({"user": "42", "exp": datetime.utcnow() + timedelta(hours=1)})
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401

    def test_non_numeric_sub_raises_401(self):
        token = self._make_token({"sub": "not-a-number", "exp": datetime.utcnow() + timedelta(hours=1)})
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# get_workspace_id tests
# ---------------------------------------------------------------------------

class TestGetWorkspaceId:
    def test_valid_workspace_id_returns_uuid(self):
        from uuid import UUID
        result = get_workspace_id("550e8400-e29b-41d4-a716-446655440000")
        assert result == UUID("550e8400-e29b-41d4-a716-446655440000")

    def test_missing_workspace_id_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            get_workspace_id(None)
        assert exc_info.value.status_code == 400
        assert "X-Workspace-Id" in exc_info.value.detail

    def test_invalid_workspace_id_format_raises_400(self):
        with pytest.raises(HTTPException) as exc_info:
            get_workspace_id("not-a-uuid")
        assert exc_info.value.status_code == 400
        assert "Invalid" in exc_info.value.detail


# ---------------------------------------------------------------------------
# verify_internal_token tests
# ---------------------------------------------------------------------------

class TestVerifyInternalToken:
    def _make_request(self, token=None):
        request = MagicMock()
        request.headers = {"X-Internal-Token": token} if token else {}
        return request

    def test_valid_token_passes(self):
        request = self._make_request("test-internal-token")
        # Should not raise
        verify_internal_token(request)

    def test_missing_token_raises_403(self):
        request = self._make_request(None)
        with pytest.raises(HTTPException) as exc_info:
            verify_internal_token(request)
        assert exc_info.value.status_code == 403
        assert "unauthorized" in exc_info.value.detail.lower()

    def test_wrong_token_raises_403(self):
        request = self._make_request("wrong-token")
        with pytest.raises(HTTPException) as exc_info:
            verify_internal_token(request)
        assert exc_info.value.status_code == 403
        assert "Unauthorized" in exc_info.value.detail


# ---------------------------------------------------------------------------
# exception_handlers tests (async handlers tested via direct calls)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_request():
    req = MagicMock()
    req.url.path = "/test"
    req.method = "GET"
    return req


import asyncio
import json as _json


def _run(coro):
    """Run an async coroutine synchronously for testing."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestExceptionHandlers:
    def test_standardized_error_handler(self, mock_request):
        exc = ExpenseValidationError("test error", ErrorCode.VALIDATION_ERROR)
        response = _run(standardized_error_handler(mock_request, exc))
        assert response.status_code == 400
        body = _json.loads(response.body)
        assert "error" in body
        assert "errorCode" in body

    def test_expense_not_found_handler(self, mock_request):
        exc = ExpenseNotFoundError(expense_id=42)
        response = _run(expense_not_found_handler(mock_request, exc))
        assert response.status_code == 404

    def test_expense_validation_handler(self, mock_request):
        exc = ExpenseValidationError("validation failed", ErrorCode.VALIDATION_ERROR)
        response = _run(expense_validation_handler(mock_request, exc))
        assert response.status_code == 400

    def test_expense_amount_handler(self, mock_request):
        exc = ExpenseAmountError(amount=1000000.0, max_amount=999999.99)
        response = _run(expense_amount_handler(mock_request, exc))
        assert response.status_code == 400

    def test_expense_date_handler(self, mock_request):
        exc = ExpenseDateError("2099-01-01", "future")
        response = _run(expense_date_handler(mock_request, exc))
        assert response.status_code == 400

    def test_expense_description_handler(self, mock_request):
        exc = ExpenseDescriptionError(length=600, max_length=500)
        response = _run(expense_description_handler(mock_request, exc))
        assert response.status_code == 400

    def test_external_service_handler(self, mock_request):
        exc = ExternalServiceError("test-service", "service down")
        response = _run(external_service_handler(mock_request, exc))
        assert response.status_code == 503

    def test_http_exception_handler_plain_string(self, mock_request):
        exc = HTTPException(status_code=404, detail="Not found")
        response = _run(http_exception_handler(mock_request, exc))
        assert response.status_code == 404
        body = _json.loads(response.body)
        assert "error" in body
        assert "errorCode" in body

    def test_http_exception_handler_already_standardized(self, mock_request):
        """When detail is already a standardized dict, it should be passed through as-is."""
        standardized_detail = {
            "error": "Custom error",
            "errorCode": "SOME_CODE"
        }
        exc = HTTPException(status_code=422, detail=standardized_detail)
        response = _run(http_exception_handler(mock_request, exc))
        assert response.status_code == 422
        body = _json.loads(response.body)
        assert body["error"] == "Custom error"

    def test_custom_validation_exception_handler_empty_errors(self, mock_request):
        """Edge case: empty validation errors list."""
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = []
        response = _run(custom_validation_exception_handler(mock_request, exc))
        assert response.status_code == 400
        body = _json.loads(response.body)
        assert "Validation error" in body["error"]

    def test_custom_validation_handler_missing_field(self, mock_request):
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "amount"), "type": "missing", "msg": "field required"}
        ]
        response = _run(custom_validation_exception_handler(mock_request, exc))
        assert response.status_code == 400
        body = _json.loads(response.body)
        assert body["errorCode"] == ErrorCode.MISSING_REQUIRED_FIELD.value

    def test_custom_validation_handler_greater_than(self, mock_request):
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "amount"), "type": "greater_than", "msg": "must be > 0"}
        ]
        response = _run(custom_validation_exception_handler(mock_request, exc))
        assert response.status_code == 400
        body = _json.loads(response.body)
        assert body["errorCode"] == ErrorCode.INVALID_FIELD_VALUE.value

    def test_custom_validation_handler_less_than_equal(self, mock_request):
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "amount"), "type": "less_than_equal", "msg": "too large"}
        ]
        response = _run(custom_validation_exception_handler(mock_request, exc))
        assert response.status_code == 400
        body = _json.loads(response.body)
        assert "exceeds maximum allowed value" in body["error"]

    def test_custom_validation_handler_string_too_long(self, mock_request):
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "description"), "type": "string_too_long", "msg": "too long"}
        ]
        response = _run(custom_validation_exception_handler(mock_request, exc))
        assert response.status_code == 400
        body = _json.loads(response.body)
        assert "exceeds maximum length" in body["error"]

    def test_custom_validation_handler_other_type(self, mock_request):
        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = [
            {"loc": ("body", "date"), "type": "date_from_datetime_inexact", "msg": "invalid date format"}
        ]
        response = _run(custom_validation_exception_handler(mock_request, exc))
        assert response.status_code == 400
        body = _json.loads(response.body)
        assert body["errorCode"] == ErrorCode.INVALID_FIELD_VALUE.value


# ---------------------------------------------------------------------------
# Integration: verify dependencies via HTTP client
# ---------------------------------------------------------------------------

@pytest.fixture
def http_client():
    with TestClient(app) as c:
        yield c


class TestDependencyIntegration:
    def test_missing_workspace_header_when_override_removed_returns_400(self, http_client):
        """Temporarily remove the conftest workspace override to test real dependency."""
        from app.dependencies import get_workspace_id as gw
        # Save the conftest override
        orig_override = app.dependency_overrides.get(gw)
        # Remove the override to test the real dependency
        app.dependency_overrides.pop(gw, None)
        try:
            with patch("shared.auth.dependencies.decode_token", return_value=1):
                response = http_client.get(
                    "/expenses/",
                    headers={"Authorization": "Bearer dummy"}
                )
            assert response.status_code == 400
            assert "X-Workspace-Id" in response.json()["error"]
        finally:
            if orig_override is not None:
                app.dependency_overrides[gw] = orig_override

    def test_invalid_workspace_id_when_override_removed_returns_400(self, http_client):
        """Temporarily remove conftest workspace override to test invalid UUID."""
        from app.dependencies import get_workspace_id as gw
        orig_override = app.dependency_overrides.get(gw)
        app.dependency_overrides.pop(gw, None)
        try:
            with patch("shared.auth.dependencies.decode_token", return_value=1):
                response = http_client.get(
                    "/expenses/",
                    headers={
                        "Authorization": "Bearer dummy",
                        "X-Workspace-Id": "not-a-valid-uuid"
                    }
                )
            assert response.status_code == 400
        finally:
            if orig_override is not None:
                app.dependency_overrides[gw] = orig_override

    def test_missing_auth_token_returns_403(self, http_client):
        response = http_client.get(
            "/expenses/",
            headers={"X-Workspace-Id": "550e8400-e29b-41d4-a716-446655440000"}
        )
        assert response.status_code == 403

    def test_invalid_jwt_returns_401_or_400(self, http_client):
        response = http_client.get(
            "/expenses/",
            headers={
                "Authorization": "Bearer not.a.real.token",
                "X-Workspace-Id": "550e8400-e29b-41d4-a716-446655440000"
            }
        )
        assert response.status_code in (401, 400)  # JWT decode error -> 401
