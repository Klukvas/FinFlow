"""
Unit tests for exception handlers - verifies HTTP responses from custom exceptions.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException, status

from app.exception_handlers import (
    currency_error_handler,
    http_exception_handler,
    general_exception_handler,
)
from app.exceptions import (
    CurrencyError,
    UnsupportedCurrencyError,
    CurrencyServiceUnavailableError,
    CurrencyConversionFailedError,
    CurrencyRatesFetchFailedError,
    CurrencyCacheError,
    CurrencyValidationError,
    ExternalApiError,
    RedisConnectionError,
)


@pytest.fixture
def mock_request():
    """Return a mock Request object."""
    return MagicMock()


# ---------------------------------------------------------------------------
# currency_error_handler
# ---------------------------------------------------------------------------

class TestCurrencyErrorHandler:
    @pytest.mark.asyncio
    async def test_unsupported_currency_returns_400(self, mock_request):
        exc = UnsupportedCurrencyError("XYZ")
        response = await currency_error_handler(mock_request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_validation_error_returns_400(self, mock_request):
        exc = CurrencyValidationError("amount", -1.0, "must be positive")
        response = await currency_error_handler(mock_request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_service_unavailable_returns_503(self, mock_request):
        exc = CurrencyServiceUnavailableError("fetching rates")
        response = await currency_error_handler(mock_request, exc)
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_conversion_failed_returns_503(self, mock_request):
        exc = CurrencyConversionFailedError("USD", "EUR")
        response = await currency_error_handler(mock_request, exc)
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_rates_fetch_failed_returns_503(self, mock_request):
        exc = CurrencyRatesFetchFailedError("USD")
        response = await currency_error_handler(mock_request, exc)
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_cache_error_returns_503(self, mock_request):
        exc = CurrencyCacheError("get", "currency:rates:USD")
        response = await currency_error_handler(mock_request, exc)
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_external_api_error_returns_503(self, mock_request):
        exc = ExternalApiError("https://api.example.com", 500)
        response = await currency_error_handler(mock_request, exc)
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_redis_connection_error_returns_503(self, mock_request):
        exc = RedisConnectionError("redis://localhost:6379")
        response = await currency_error_handler(mock_request, exc)
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_base_currency_error_returns_500(self, mock_request):
        """Unknown CurrencyError subclass defaults to 500."""
        exc = CurrencyError("unknown error", "UNKNOWN_CODE")
        response = await currency_error_handler(mock_request, exc)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_response_body_contains_error_dict(self, mock_request):
        exc = UnsupportedCurrencyError("XYZ")
        response = await currency_error_handler(mock_request, exc)
        # JSONResponse body is the error dict
        import json
        body = json.loads(response.body)
        assert body["errorCode"] == "UNSUPPORTED_CURRENCY"
        assert body["currency"] == "XYZ"


# ---------------------------------------------------------------------------
# http_exception_handler
# ---------------------------------------------------------------------------

class TestHttpExceptionHandler:
    @pytest.mark.asyncio
    async def test_string_detail(self, mock_request):
        exc = HTTPException(status_code=404, detail="Not Found")
        response = await http_exception_handler(mock_request, exc)
        assert response.status_code == 404
        import json
        body = json.loads(response.body)
        assert body["error"] == "Not Found"
        assert body["errorCode"] == "HTTP_ERROR"

    @pytest.mark.asyncio
    async def test_dict_detail(self, mock_request):
        detail = {"error": "Custom error", "errorCode": "CUSTOM_CODE"}
        exc = HTTPException(status_code=400, detail=detail)
        response = await http_exception_handler(mock_request, exc)
        assert response.status_code == 400
        import json
        body = json.loads(response.body)
        assert body["error"] == "Custom error"
        assert body["errorCode"] == "CUSTOM_CODE"

    @pytest.mark.asyncio
    async def test_422_validation(self, mock_request):
        exc = HTTPException(status_code=422, detail="Validation failed")
        response = await http_exception_handler(mock_request, exc)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# general_exception_handler
# ---------------------------------------------------------------------------

class TestGeneralExceptionHandler:
    @pytest.mark.asyncio
    async def test_returns_500(self, mock_request):
        exc = RuntimeError("unexpected crash")
        response = await general_exception_handler(mock_request, exc)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_response_body_format(self, mock_request):
        exc = ValueError("bad value")
        response = await general_exception_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert body["error"] == "Internal server error occurred"
        assert body["errorCode"] == "INTERNAL_SERVER_ERROR"
        assert body["details"]["type"] == "ValueError"
        assert body["details"]["message"] == "bad value"

    @pytest.mark.asyncio
    async def test_does_not_leak_traceback(self, mock_request):
        """General handler should not include traceback in response."""
        exc = RuntimeError("secret internal error")
        response = await general_exception_handler(mock_request, exc)
        import json
        body = json.loads(response.body)
        assert "traceback" not in body
        assert "stack" not in body
