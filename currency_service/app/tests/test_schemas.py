"""
Unit tests for Pydantic schemas - input validation and serialization.
"""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.schemas.currency import (
    CurrencyInfo,
    ExchangeRate,
    ConversionRequest,
    ConversionResponse,
    CurrencyRatesResponse,
    SupportedCurrenciesResponse,
    HealthResponse,
)


# ---------------------------------------------------------------------------
# CurrencyInfo
# ---------------------------------------------------------------------------

class TestCurrencyInfo:
    def test_valid_currency_info(self):
        info = CurrencyInfo(
            code="USD", name="US Dollar", symbol="$", flag="US", locale="en-US"
        )
        assert info.code == "USD"
        assert info.name == "US Dollar"
        assert info.symbol == "$"

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            CurrencyInfo(code="USD", name="US Dollar", symbol="$")  # missing flag, locale

    def test_serialization(self):
        info = CurrencyInfo(
            code="EUR", name="Euro", symbol="E", flag="EU", locale="de-DE"
        )
        data = info.model_dump()
        assert data["code"] == "EUR"
        assert "name" in data
        assert "symbol" in data
        assert "flag" in data
        assert "locale" in data


# ---------------------------------------------------------------------------
# ExchangeRate
# ---------------------------------------------------------------------------

class TestExchangeRate:
    def test_valid_exchange_rate(self):
        now = datetime.now(timezone.utc)
        rate = ExchangeRate(
            from_currency="USD", to_currency="EUR", rate=0.85, timestamp=now
        )
        assert rate.from_currency == "USD"
        assert rate.to_currency == "EUR"
        assert rate.rate == 0.85

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            ExchangeRate(from_currency="USD")


# ---------------------------------------------------------------------------
# ConversionRequest
# ---------------------------------------------------------------------------

class TestConversionRequest:
    def test_valid_request(self):
        req = ConversionRequest(
            amount=100.0, from_currency="USD", to_currency="EUR"
        )
        assert req.amount == 100.0
        assert req.from_currency == "USD"
        assert req.to_currency == "EUR"

    def test_currency_code_min_length(self):
        with pytest.raises(ValidationError):
            ConversionRequest(amount=100.0, from_currency="US", to_currency="EUR")

    def test_currency_code_max_length(self):
        with pytest.raises(ValidationError):
            ConversionRequest(amount=100.0, from_currency="USDD", to_currency="EUR")

    def test_negative_amount_passes_schema(self):
        """Schema allows negative amounts; router validates business rules."""
        req = ConversionRequest(amount=-10.0, from_currency="USD", to_currency="EUR")
        assert req.amount == -10.0

    def test_zero_amount(self):
        req = ConversionRequest(amount=0.0, from_currency="USD", to_currency="EUR")
        assert req.amount == 0.0

    def test_large_amount(self):
        req = ConversionRequest(amount=999999999.99, from_currency="USD", to_currency="EUR")
        assert req.amount == 999999999.99

    def test_missing_amount(self):
        with pytest.raises(ValidationError):
            ConversionRequest(from_currency="USD", to_currency="EUR")

    def test_missing_from_currency(self):
        with pytest.raises(ValidationError):
            ConversionRequest(amount=100.0, to_currency="EUR")

    def test_missing_to_currency(self):
        with pytest.raises(ValidationError):
            ConversionRequest(amount=100.0, from_currency="USD")


# ---------------------------------------------------------------------------
# ConversionResponse
# ---------------------------------------------------------------------------

class TestConversionResponse:
    def test_valid_response(self):
        now = datetime.now(timezone.utc)
        resp = ConversionResponse(
            amount=100.0,
            converted_amount=85.0,
            from_currency="USD",
            to_currency="EUR",
            rate=0.85,
            timestamp=now,
        )
        assert resp.amount == 100.0
        assert resp.converted_amount == 85.0
        assert resp.rate == 0.85

    def test_serialization(self):
        now = datetime.now(timezone.utc)
        resp = ConversionResponse(
            amount=100.0,
            converted_amount=85.0,
            from_currency="USD",
            to_currency="EUR",
            rate=0.85,
            timestamp=now,
        )
        data = resp.model_dump()
        assert "amount" in data
        assert "converted_amount" in data
        assert "rate" in data
        assert "timestamp" in data


# ---------------------------------------------------------------------------
# CurrencyRatesResponse
# ---------------------------------------------------------------------------

class TestCurrencyRatesResponse:
    def test_valid_response(self):
        now = datetime.now(timezone.utc)
        resp = CurrencyRatesResponse(
            base_currency="USD",
            rates={"EUR": 0.85, "GBP": 0.73},
            timestamp=now,
        )
        assert resp.base_currency == "USD"
        assert len(resp.rates) == 2

    def test_empty_rates(self):
        now = datetime.now(timezone.utc)
        resp = CurrencyRatesResponse(
            base_currency="USD", rates={}, timestamp=now
        )
        assert resp.rates == {}


# ---------------------------------------------------------------------------
# SupportedCurrenciesResponse
# ---------------------------------------------------------------------------

class TestSupportedCurrenciesResponse:
    def test_valid_response(self):
        currencies = [
            CurrencyInfo(code="USD", name="US Dollar", symbol="$", flag="US", locale="en-US"),
        ]
        resp = SupportedCurrenciesResponse(currencies=currencies, total_count=1)
        assert resp.total_count == 1
        assert len(resp.currencies) == 1

    def test_empty_currencies(self):
        resp = SupportedCurrenciesResponse(currencies=[], total_count=0)
        assert resp.total_count == 0
        assert len(resp.currencies) == 0


# ---------------------------------------------------------------------------
# HealthResponse
# ---------------------------------------------------------------------------

class TestHealthResponse:
    def test_healthy_response(self):
        now = datetime.now(timezone.utc)
        resp = HealthResponse(
            status="healthy",
            timestamp=now,
            redis_connected=True,
            api_accessible=True,
        )
        assert resp.status == "healthy"
        assert resp.redis_connected is True

    def test_unhealthy_response(self):
        now = datetime.now(timezone.utc)
        resp = HealthResponse(
            status="unhealthy",
            timestamp=now,
            redis_connected=False,
            api_accessible=False,
        )
        assert resp.status == "unhealthy"

    def test_degraded_response(self):
        now = datetime.now(timezone.utc)
        resp = HealthResponse(
            status="degraded",
            timestamp=now,
            redis_connected=True,
            api_accessible=False,
        )
        assert resp.status == "degraded"
