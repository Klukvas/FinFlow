"""
Tests for app/exception_handlers.py — FastAPI exception handler functions.
"""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette import status

from app.exception_handlers import (
    custom_validation_exception_handler,
    account_not_found_handler,
    account_validation_handler,
    account_ownership_handler,
    account_archived_handler,
    account_balance_handler,
    account_read_only_excess_handler,
    external_service_handler,
    http_exception_handler,
)
from app.exceptions import (
    AccountNotFoundError,
    AccountValidationError,
    AccountOwnershipError,
    AccountArchivedError,
    AccountBalanceError,
    AccountReadOnlyExcessError,
    ExternalServiceError,
    AccountErrorCode,
)


@pytest.fixture
def mock_request():
    return MagicMock()


class TestCustomValidationExceptionHandler:
    def test_returns_422(self, mock_request):
        exc = RequestValidationError(errors=[{"msg": "field required"}])
        response = custom_validation_exception_handler(mock_request, exc)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_response_body(self, mock_request):
        exc = RequestValidationError(errors=[{"msg": "test"}])
        response = custom_validation_exception_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert body["error"] == "Invalid request data"
        assert body["errorCode"] == AccountErrorCode.VALIDATION_ERROR


class TestAccountNotFoundHandler:
    def test_returns_404(self, mock_request):
        exc = AccountNotFoundError(42)
        response = account_not_found_handler(mock_request, exc)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_response_contains_error(self, mock_request):
        exc = AccountNotFoundError(42)
        response = account_not_found_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert "42" in body["error"]
        assert body["errorCode"] == AccountErrorCode.ACCOUNT_NOT_FOUND


class TestAccountValidationHandler:
    def test_returns_400(self, mock_request):
        exc = AccountValidationError("bad input")
        response = account_validation_handler(mock_request, exc)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_response_message(self, mock_request):
        exc = AccountValidationError("invalid name", AccountErrorCode.INVALID_ACCOUNT_NAME)
        response = account_validation_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert body["error"] == "invalid name"
        assert body["errorCode"] == AccountErrorCode.INVALID_ACCOUNT_NAME


class TestAccountOwnershipHandler:
    def test_returns_403(self, mock_request):
        exc = AccountOwnershipError(10, 5)
        response = account_ownership_handler(mock_request, exc)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_response_fields(self, mock_request):
        exc = AccountOwnershipError(10, 5)
        response = account_ownership_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert body["errorCode"] == AccountErrorCode.ACCOUNT_NOT_OWNED


class TestAccountArchivedHandler:
    def test_returns_400(self, mock_request):
        exc = AccountArchivedError(7)
        response = account_archived_handler(mock_request, exc)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_response_message(self, mock_request):
        exc = AccountArchivedError(7)
        response = account_archived_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert "7" in body["error"]
        assert body["errorCode"] == AccountErrorCode.ACCOUNT_ARCHIVED


class TestAccountBalanceHandler:
    def test_returns_400(self, mock_request):
        exc = AccountBalanceError("invalid")
        response = account_balance_handler(mock_request, exc)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_response_fields(self, mock_request):
        exc = AccountBalanceError("overflow", AccountErrorCode.INVALID_BALANCE)
        response = account_balance_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert body["error"] == "overflow"
        assert body["errorCode"] == AccountErrorCode.INVALID_BALANCE


class TestAccountReadOnlyExcessHandler:
    def test_returns_403(self, mock_request):
        exc = AccountReadOnlyExcessError(10, 6, 5)
        response = account_read_only_excess_handler(mock_request, exc)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_response_includes_limit_info(self, mock_request):
        exc = AccountReadOnlyExcessError(10, 6, 5)
        response = account_read_only_excess_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert body["feature"] == "accounts"
        assert body["current_count"] == 6
        assert body["limit"] == 5


class TestExternalServiceHandler:
    def test_returns_503(self, mock_request):
        exc = ExternalServiceError("expense-service", "timeout")
        response = external_service_handler(mock_request, exc)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_response_fields(self, mock_request):
        exc = ExternalServiceError("income-service", "connection refused")
        response = external_service_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert body["errorCode"] == AccountErrorCode.EXTERNAL_SERVICE_ERROR


class TestHttpExceptionHandler:
    def test_returns_correct_status(self, mock_request):
        exc = HTTPException(status_code=429, detail="Too many requests")
        response = http_exception_handler(mock_request, exc)
        assert response.status_code == 429

    def test_response_body(self, mock_request):
        exc = HTTPException(status_code=500, detail="Server error")
        response = http_exception_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert body["error"] == "Server error"
        assert body["errorCode"] == AccountErrorCode.UNKNOWN_ERROR
