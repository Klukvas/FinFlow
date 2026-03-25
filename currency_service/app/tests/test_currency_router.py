"""
Unit tests for currency router - API endpoint layer.
Tests HTTP endpoints with mocked CurrencyService dependency.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.schemas.currency import (
    CurrencyInfo,
    ConversionResponse,
    CurrencyRatesResponse,
)
from app.exceptions import (
    CurrencyServiceUnavailableError,
    CurrencyRatesFetchFailedError,
    CurrencyConversionFailedError,
    UnsupportedCurrencyError,
    CurrencyValidationError,
)


# ---------------------------------------------------------------------------
# GET /api/v1/currencies
# ---------------------------------------------------------------------------

class TestGetSupportedCurrencies:
    def test_success(self, client, mock_currency_service, sample_currencies):
        """Endpoint returns list of supported currencies."""
        response = client.get("/api/v1/currencies")

        assert response.status_code == 200
        data = response.json()
        assert "currencies" in data
        assert "total_count" in data
        assert data["total_count"] == len(sample_currencies)
        assert len(data["currencies"]) == len(sample_currencies)

    def test_returns_currency_fields(self, client, mock_currency_service, sample_currencies):
        """Each currency should have code, name, symbol, flag, locale fields."""
        response = client.get("/api/v1/currencies")

        data = response.json()
        currency = data["currencies"][0]
        assert "code" in currency
        assert "name" in currency
        assert "symbol" in currency
        assert "flag" in currency
        assert "locale" in currency

    def test_service_exception_returns_503(self, client, mock_currency_service):
        """When the service raises an exception, return 503."""
        mock_currency_service.get_supported_currencies.side_effect = Exception("DB down")

        response = client.get("/api/v1/currencies")

        assert response.status_code == 503
        data = response.json()
        assert data["errorCode"] == "CURRENCY_SERVICE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# GET /api/v1/rates
# ---------------------------------------------------------------------------

class TestGetCurrencyRates:
    def test_success_default_base(self, client, mock_currency_service):
        """Endpoint returns rates with default USD base."""
        mock_currency_service.get_currency_rates.return_value = CurrencyRatesResponse(
            base_currency="USD",
            rates={"EUR": 0.85, "GBP": 0.73},
            timestamp=datetime.now(timezone.utc)
        )

        response = client.get("/api/v1/rates")

        assert response.status_code == 200
        data = response.json()
        assert data["base_currency"] == "USD"
        assert "EUR" in data["rates"]

    def test_success_custom_base(self, client, mock_currency_service):
        """Endpoint returns rates for a custom base currency."""
        mock_currency_service.get_currency_rates.return_value = CurrencyRatesResponse(
            base_currency="EUR",
            rates={"USD": 1.18, "GBP": 0.86},
            timestamp=datetime.now(timezone.utc)
        )

        response = client.get("/api/v1/rates?base_currency=EUR")

        assert response.status_code == 200
        data = response.json()
        assert data["base_currency"] == "EUR"

    def test_returns_none_gives_503(self, client, mock_currency_service):
        """When service returns None, return 503 with rates fetch error."""
        mock_currency_service.get_currency_rates.return_value = None

        response = client.get("/api/v1/rates")

        assert response.status_code == 503
        data = response.json()
        assert data["errorCode"] == "CURRENCY_RATES_FETCH_FAILED"

    def test_service_exception_returns_503(self, client, mock_currency_service):
        """When service raises an exception, return 503."""
        mock_currency_service.get_currency_rates.side_effect = RuntimeError("unexpected")

        response = client.get("/api/v1/rates")

        assert response.status_code == 503
        data = response.json()
        assert data["errorCode"] == "CURRENCY_RATES_FETCH_FAILED"


# ---------------------------------------------------------------------------
# POST /api/v1/convert
# ---------------------------------------------------------------------------

class TestConvertCurrency:
    def test_success(self, client, mock_currency_service, sample_currencies):
        """Successful conversion returns correct response."""
        mock_currency_service.convert_amount.return_value = ConversionResponse(
            amount=100.0,
            converted_amount=85.0,
            from_currency="USD",
            to_currency="EUR",
            rate=0.85,
            timestamp=datetime.now(timezone.utc)
        )

        response = client.post(
            "/api/v1/convert",
            json={"amount": 100.0, "from_currency": "USD", "to_currency": "EUR"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 100.0
        assert data["converted_amount"] == 85.0
        assert data["rate"] == 0.85
        assert data["from_currency"] == "USD"
        assert data["to_currency"] == "EUR"

    def test_negative_amount_returns_400(self, client, mock_currency_service, sample_currencies):
        """Negative amount should return 400 validation error."""
        response = client.post(
            "/api/v1/convert",
            json={"amount": -10.0, "from_currency": "USD", "to_currency": "EUR"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["errorCode"] == "CURRENCY_VALIDATION_ERROR"

    def test_unsupported_source_currency_returns_400(self, client, mock_currency_service, sample_currencies):
        """Unsupported source currency should return 400."""
        response = client.post(
            "/api/v1/convert",
            json={"amount": 100.0, "from_currency": "XYZ", "to_currency": "EUR"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["errorCode"] == "UNSUPPORTED_CURRENCY"

    def test_unsupported_target_currency_returns_400(self, client, mock_currency_service, sample_currencies):
        """Unsupported target currency should return 400."""
        response = client.post(
            "/api/v1/convert",
            json={"amount": 100.0, "from_currency": "USD", "to_currency": "XYZ"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["errorCode"] == "UNSUPPORTED_CURRENCY"

    def test_conversion_returns_none_gives_503(self, client, mock_currency_service, sample_currencies):
        """When conversion fails (returns None), return 503."""
        mock_currency_service.convert_amount.return_value = None

        response = client.post(
            "/api/v1/convert",
            json={"amount": 100.0, "from_currency": "USD", "to_currency": "EUR"}
        )

        assert response.status_code == 503
        data = response.json()
        assert data["errorCode"] == "CURRENCY_CONVERSION_FAILED"

    def test_service_exception_returns_503(self, client, mock_currency_service, sample_currencies):
        """When service raises unexpected error, return 503."""
        mock_currency_service.convert_amount.side_effect = RuntimeError("unexpected")

        response = client.post(
            "/api/v1/convert",
            json={"amount": 100.0, "from_currency": "USD", "to_currency": "EUR"}
        )

        assert response.status_code == 503
        data = response.json()
        assert data["errorCode"] == "CURRENCY_CONVERSION_FAILED"

    def test_invalid_currency_code_too_short(self, client, mock_currency_service):
        """Currency codes shorter than 3 chars should fail Pydantic validation."""
        response = client.post(
            "/api/v1/convert",
            json={"amount": 100.0, "from_currency": "US", "to_currency": "EUR"}
        )

        # Pydantic validation returns 422
        assert response.status_code == 422

    def test_invalid_currency_code_too_long(self, client, mock_currency_service):
        """Currency codes longer than 3 chars should fail Pydantic validation."""
        response = client.post(
            "/api/v1/convert",
            json={"amount": 100.0, "from_currency": "USDD", "to_currency": "EUR"}
        )

        assert response.status_code == 422

    def test_missing_amount_field(self, client, mock_currency_service):
        """Missing amount field should return 422."""
        response = client.post(
            "/api/v1/convert",
            json={"from_currency": "USD", "to_currency": "EUR"}
        )

        assert response.status_code == 422

    def test_missing_from_currency(self, client, mock_currency_service):
        """Missing from_currency should return 422."""
        response = client.post(
            "/api/v1/convert",
            json={"amount": 100.0, "to_currency": "EUR"}
        )

        assert response.status_code == 422

    def test_missing_to_currency(self, client, mock_currency_service):
        """Missing to_currency should return 422."""
        response = client.post(
            "/api/v1/convert",
            json={"amount": 100.0, "from_currency": "USD"}
        )

        assert response.status_code == 422

    def test_zero_amount_succeeds(self, client, mock_currency_service, sample_currencies):
        """Zero amount should pass validation (only negative is rejected)."""
        mock_currency_service.convert_amount.return_value = ConversionResponse(
            amount=0.0,
            converted_amount=0.0,
            from_currency="USD",
            to_currency="EUR",
            rate=0.85,
            timestamp=datetime.now(timezone.utc)
        )

        response = client.post(
            "/api/v1/convert",
            json={"amount": 0.0, "from_currency": "USD", "to_currency": "EUR"}
        )

        assert response.status_code == 200

    def test_same_currency_conversion(self, client, mock_currency_service, sample_currencies):
        """Converting same currency should succeed."""
        mock_currency_service.convert_amount.return_value = ConversionResponse(
            amount=100.0,
            converted_amount=100.0,
            from_currency="USD",
            to_currency="USD",
            rate=1.0,
            timestamp=datetime.now(timezone.utc)
        )

        response = client.post(
            "/api/v1/convert",
            json={"amount": 100.0, "from_currency": "USD", "to_currency": "USD"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rate"] == 1.0


# ---------------------------------------------------------------------------
# POST /api/v1/currencies/refresh
# ---------------------------------------------------------------------------

class TestRefreshCurrencies:
    def test_success(self, client, mock_currency_service, sample_currencies):
        """Refresh should return updated currencies list."""
        response = client.post("/api/v1/currencies/refresh")

        assert response.status_code == 200
        data = response.json()
        assert "currencies" in data
        assert "total_count" in data

    def test_api_returns_none_uses_fallback(self, client, mock_currency_service, sample_currencies):
        """When API returns None, fallback list should be used."""
        mock_currency_service._fetch_currencies_from_api.return_value = None

        response = client.post("/api/v1/currencies/refresh")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == len(sample_currencies)

    def test_exception_returns_503(self, client, mock_currency_service):
        """When refresh fails, return 503."""
        mock_currency_service._fetch_currencies_from_api.side_effect = Exception("API down")

        response = client.post("/api/v1/currencies/refresh")

        assert response.status_code == 503
        data = response.json()
        assert data["errorCode"] == "CURRENCY_SERVICE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# GET /api/v1/health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_healthy(self, client, mock_currency_service):
        """When all services are healthy, status should be healthy."""
        mock_currency_service.health_check.return_value = {
            "redis_connected": True,
            "api_accessible": True,
        }

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["redis_connected"] is True
        assert data["api_accessible"] is True

    def test_degraded(self, client, mock_currency_service):
        """When one service is down, status should be degraded."""
        mock_currency_service.health_check.return_value = {
            "redis_connected": True,
            "api_accessible": False,
        }

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"

    def test_exception_returns_unhealthy(self, client, mock_currency_service):
        """When health check itself fails, return unhealthy."""
        mock_currency_service.health_check.side_effect = Exception("check failed")

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["redis_connected"] is False
        assert data["api_accessible"] is False


# ---------------------------------------------------------------------------
# Root and health endpoints on the main app
# ---------------------------------------------------------------------------

class TestRootEndpoints:
    def test_root_endpoint(self, client):
        """Root endpoint should return service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Currency Service API"
        assert "version" in data
        assert data["status"] == "running"

    def test_health_root_endpoint(self, client):
        """Main health check endpoint should return healthy."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "currency-service"
