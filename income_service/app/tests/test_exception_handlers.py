"""Tests for app/exception_handlers.py — exception-to-response mapping."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

from app.exception_handlers import (
    custom_validation_exception_handler,
    income_not_found_handler,
    income_validation_handler,
    income_amount_handler,
    income_date_handler,
    income_description_handler,
    external_service_handler,
    http_exception_handler,
)
from app.exceptions import (
    IncomeNotFoundError,
    IncomeValidationError,
    IncomeAmountError,
    IncomeDateError,
    IncomeDescriptionError,
    ExternalServiceError,
    IncomeErrorCodes,
)


@pytest.fixture
def mock_request():
    """A minimal mock Request object."""
    return MagicMock()


# ---------------------------------------------------------------------------
# custom_validation_exception_handler
# ---------------------------------------------------------------------------
class TestCustomValidationExceptionHandler:
    @pytest.mark.asyncio
    async def test_returns_422_with_details(self, mock_request):
        errors = [
            {"loc": ("body", "amount"), "msg": "field required", "type": "value_error.missing"}
        ]
        exc = RequestValidationError(errors=errors)
        response = await custom_validation_exception_handler(mock_request, exc)

        assert response.status_code == 422
        import json
        body = json.loads(response.body)
        assert body["error"] == "Validation error"
        assert body["errorCode"] == IncomeErrorCodes.VALIDATION_ERROR
        assert len(body["details"]) == 1
        assert "amount" in body["details"][0]

    @pytest.mark.asyncio
    async def test_multiple_validation_errors(self, mock_request):
        errors = [
            {"loc": ("body", "amount"), "msg": "field required", "type": "value_error.missing"},
            {"loc": ("body", "currency"), "msg": "too short", "type": "value_error"},
        ]
        exc = RequestValidationError(errors=errors)
        response = await custom_validation_exception_handler(mock_request, exc)

        import json
        body = json.loads(response.body)
        assert len(body["details"]) == 2


# ---------------------------------------------------------------------------
# income_not_found_handler
# ---------------------------------------------------------------------------
class TestIncomeNotFoundHandler:
    @pytest.mark.asyncio
    async def test_returns_404(self, mock_request):
        exc = IncomeNotFoundError("Income 99 not found")
        response = await income_not_found_handler(mock_request, exc)

        assert response.status_code == 404
        import json
        body = json.loads(response.body)
        assert "99" in body["error"]
        assert body["errorCode"] == IncomeErrorCodes.INCOME_NOT_FOUND


# ---------------------------------------------------------------------------
# income_validation_handler
# ---------------------------------------------------------------------------
class TestIncomeValidationHandler:
    @pytest.mark.asyncio
    async def test_returns_400(self, mock_request):
        exc = IncomeValidationError("Bad data")
        response = await income_validation_handler(mock_request, exc)

        assert response.status_code == 400
        import json
        body = json.loads(response.body)
        assert body["error"] == "Bad data"
        assert body["errorCode"] == IncomeErrorCodes.INCOME_VALIDATION_FAILED


# ---------------------------------------------------------------------------
# income_amount_handler
# ---------------------------------------------------------------------------
class TestIncomeAmountHandler:
    @pytest.mark.asyncio
    async def test_returns_400_with_amount_code(self, mock_request):
        exc = IncomeAmountError("Negative amount", IncomeErrorCodes.INCOME_AMOUNT_NEGATIVE)
        response = await income_amount_handler(mock_request, exc)

        assert response.status_code == 400
        import json
        body = json.loads(response.body)
        assert body["errorCode"] == IncomeErrorCodes.INCOME_AMOUNT_NEGATIVE


# ---------------------------------------------------------------------------
# income_date_handler
# ---------------------------------------------------------------------------
class TestIncomeDateHandler:
    @pytest.mark.asyncio
    async def test_returns_400_with_date_code(self, mock_request):
        exc = IncomeDateError("Future date", IncomeErrorCodes.INCOME_DATE_FUTURE)
        response = await income_date_handler(mock_request, exc)

        assert response.status_code == 400
        import json
        body = json.loads(response.body)
        assert body["errorCode"] == IncomeErrorCodes.INCOME_DATE_FUTURE


# ---------------------------------------------------------------------------
# income_description_handler
# ---------------------------------------------------------------------------
class TestIncomeDescriptionHandler:
    @pytest.mark.asyncio
    async def test_returns_400_with_description_code(self, mock_request):
        exc = IncomeDescriptionError("Too long")
        response = await income_description_handler(mock_request, exc)

        assert response.status_code == 400
        import json
        body = json.loads(response.body)
        assert body["errorCode"] == IncomeErrorCodes.INCOME_DESCRIPTION_TOO_LONG


# ---------------------------------------------------------------------------
# external_service_handler
# ---------------------------------------------------------------------------
class TestExternalServiceHandler:
    @pytest.mark.asyncio
    async def test_returns_503(self, mock_request):
        exc = ExternalServiceError("Category service down", service="category-service")
        response = await external_service_handler(mock_request, exc)

        assert response.status_code == 503
        import json
        body = json.loads(response.body)
        assert "Category service down" in body["error"]
        assert body["errorCode"] == IncomeErrorCodes.EXTERNAL_SERVICE_UNAVAILABLE


# ---------------------------------------------------------------------------
# http_exception_handler
# ---------------------------------------------------------------------------
class TestHttpExceptionHandler:
    @pytest.mark.asyncio
    async def test_returns_matching_status_code(self, mock_request):
        exc = HTTPException(status_code=403, detail="Forbidden")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 403
        import json
        body = json.loads(response.body)
        assert body["error"] == "Forbidden"
        assert body["errorCode"] == "HTTP_403"

    @pytest.mark.asyncio
    async def test_500_error(self, mock_request):
        exc = HTTPException(status_code=500, detail="Server error")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 500
        import json
        body = json.loads(response.body)
        assert body["errorCode"] == "HTTP_500"
