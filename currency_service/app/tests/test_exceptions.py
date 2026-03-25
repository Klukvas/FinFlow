"""
Unit tests for custom exception classes and error handling.
"""
import pytest

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
from app.exceptions.currency_errors import CurrencyErrorCodes


# ---------------------------------------------------------------------------
# CurrencyError (base)
# ---------------------------------------------------------------------------

class TestCurrencyError:
    def test_base_error(self):
        error = CurrencyError("test error", "TEST_CODE")
        assert error.error == "test error"
        assert error.error_code == "TEST_CODE"
        assert error.details == {}
        assert str(error) == "test error"

    def test_base_error_with_details(self):
        details = {"key": "value"}
        error = CurrencyError("test error", "TEST_CODE", details=details)
        assert error.details == details

    def test_to_dict_without_details(self):
        error = CurrencyError("test", "CODE")
        result = error.to_dict()
        assert result == {"error": "test", "errorCode": "CODE"}

    def test_to_dict_with_details(self):
        error = CurrencyError("test", "CODE", details={"extra": "data"})
        result = error.to_dict()
        assert result["error"] == "test"
        assert result["errorCode"] == "CODE"
        assert result["extra"] == "data"


# ---------------------------------------------------------------------------
# UnsupportedCurrencyError
# ---------------------------------------------------------------------------

class TestUnsupportedCurrencyError:
    def test_source_currency(self):
        error = UnsupportedCurrencyError("XYZ", is_source=True)
        assert "source" in error.error
        assert "XYZ" in error.error
        assert error.error_code == "UNSUPPORTED_CURRENCY"
        assert error.details["currency"] == "XYZ"
        assert error.details["type"] == "source"

    def test_target_currency(self):
        error = UnsupportedCurrencyError("ABC", is_source=False)
        assert "target" in error.error
        assert "ABC" in error.error
        assert error.details["type"] == "target"

    def test_default_is_source(self):
        error = UnsupportedCurrencyError("XYZ")
        assert error.details["type"] == "source"

    def test_to_dict(self):
        error = UnsupportedCurrencyError("XYZ")
        result = error.to_dict()
        assert result["errorCode"] == "UNSUPPORTED_CURRENCY"
        assert result["currency"] == "XYZ"


# ---------------------------------------------------------------------------
# CurrencyServiceUnavailableError
# ---------------------------------------------------------------------------

class TestCurrencyServiceUnavailableError:
    def test_default_operation(self):
        error = CurrencyServiceUnavailableError()
        assert "currency operation" in error.error
        assert error.error_code == "CURRENCY_SERVICE_UNAVAILABLE"

    def test_custom_operation(self):
        error = CurrencyServiceUnavailableError("fetching rates")
        assert "fetching rates" in error.error
        assert error.details["operation"] == "fetching rates"


# ---------------------------------------------------------------------------
# CurrencyConversionFailedError
# ---------------------------------------------------------------------------

class TestCurrencyConversionFailedError:
    def test_basic(self):
        error = CurrencyConversionFailedError("USD", "EUR")
        assert "USD" in error.error
        assert "EUR" in error.error
        assert error.error_code == "CURRENCY_CONVERSION_FAILED"
        assert error.details["fromCurrency"] == "USD"
        assert error.details["toCurrency"] == "EUR"
        assert error.details["amount"] is None

    def test_with_amount(self):
        error = CurrencyConversionFailedError("USD", "EUR", 100.0)
        assert error.details["amount"] == 100.0


# ---------------------------------------------------------------------------
# CurrencyRatesFetchFailedError
# ---------------------------------------------------------------------------

class TestCurrencyRatesFetchFailedError:
    def test_default_currency(self):
        error = CurrencyRatesFetchFailedError()
        assert "USD" in error.error
        assert error.error_code == "CURRENCY_RATES_FETCH_FAILED"
        assert error.details["baseCurrency"] == "USD"

    def test_custom_currency(self):
        error = CurrencyRatesFetchFailedError("EUR")
        assert "EUR" in error.error
        assert error.details["baseCurrency"] == "EUR"


# ---------------------------------------------------------------------------
# CurrencyCacheError
# ---------------------------------------------------------------------------

class TestCurrencyCacheError:
    def test_basic(self):
        error = CurrencyCacheError("get")
        assert "get" in error.error
        assert error.error_code == "CURRENCY_CACHE_ERROR"
        assert error.details["operation"] == "get"
        assert error.details["cacheKey"] is None

    def test_with_cache_key(self):
        error = CurrencyCacheError("set", "currency:rates:USD")
        assert error.details["cacheKey"] == "currency:rates:USD"


# ---------------------------------------------------------------------------
# CurrencyValidationError
# ---------------------------------------------------------------------------

class TestCurrencyValidationError:
    def test_basic(self):
        error = CurrencyValidationError("amount", -1.0)
        assert "amount" in error.error
        assert "-1.0" in error.error
        assert error.error_code == "CURRENCY_VALIDATION_ERROR"
        assert error.details["field"] == "amount"
        assert error.details["value"] == "-1.0"

    def test_with_reason(self):
        error = CurrencyValidationError("amount", -1.0, "must be positive")
        assert "must be positive" in error.error
        assert error.details["reason"] == "must be positive"

    def test_without_reason(self):
        error = CurrencyValidationError("code", "XY")
        assert error.details["reason"] is None


# ---------------------------------------------------------------------------
# ExternalApiError
# ---------------------------------------------------------------------------

class TestExternalApiError:
    def test_basic(self):
        error = ExternalApiError("https://api.example.com/rates")
        assert "api.example.com" in error.error
        assert error.error_code == "EXTERNAL_API_ERROR"
        assert error.details["apiUrl"] == "https://api.example.com/rates"
        assert error.details["statusCode"] is None

    def test_with_status_code(self):
        error = ExternalApiError("https://api.example.com/rates", 500, "Internal Error")
        assert error.details["statusCode"] == 500
        assert error.details["responseText"] == "Internal Error"


# ---------------------------------------------------------------------------
# RedisConnectionError
# ---------------------------------------------------------------------------

class TestRedisConnectionError:
    def test_basic(self):
        error = RedisConnectionError()
        assert "Redis connection failed" in error.error
        assert error.error_code == "REDIS_CONNECTION_ERROR"
        assert error.details["redisUrl"] is None

    def test_with_url(self):
        error = RedisConnectionError("redis://localhost:6379")
        assert error.details["redisUrl"] == "redis://localhost:6379"


# ---------------------------------------------------------------------------
# CurrencyErrorCodes
# ---------------------------------------------------------------------------

class TestCurrencyErrorCodes:
    def test_all_codes_defined(self):
        assert CurrencyErrorCodes.UNSUPPORTED_CURRENCY == "UNSUPPORTED_CURRENCY"
        assert CurrencyErrorCodes.CURRENCY_SERVICE_UNAVAILABLE == "CURRENCY_SERVICE_UNAVAILABLE"
        assert CurrencyErrorCodes.CURRENCY_CONVERSION_FAILED == "CURRENCY_CONVERSION_FAILED"
        assert CurrencyErrorCodes.CURRENCY_RATES_FETCH_FAILED == "CURRENCY_RATES_FETCH_FAILED"
        assert CurrencyErrorCodes.CURRENCY_CACHE_ERROR == "CURRENCY_CACHE_ERROR"
        assert CurrencyErrorCodes.CURRENCY_VALIDATION_ERROR == "CURRENCY_VALIDATION_ERROR"
        assert CurrencyErrorCodes.EXTERNAL_API_ERROR == "EXTERNAL_API_ERROR"
        assert CurrencyErrorCodes.REDIS_CONNECTION_ERROR == "REDIS_CONNECTION_ERROR"


# ---------------------------------------------------------------------------
# Inheritance checks
# ---------------------------------------------------------------------------

class TestInheritance:
    def test_all_errors_inherit_from_currency_error(self):
        assert issubclass(UnsupportedCurrencyError, CurrencyError)
        assert issubclass(CurrencyServiceUnavailableError, CurrencyError)
        assert issubclass(CurrencyConversionFailedError, CurrencyError)
        assert issubclass(CurrencyRatesFetchFailedError, CurrencyError)
        assert issubclass(CurrencyCacheError, CurrencyError)
        assert issubclass(CurrencyValidationError, CurrencyError)
        assert issubclass(ExternalApiError, CurrencyError)
        assert issubclass(RedisConnectionError, CurrencyError)

    def test_all_errors_inherit_from_exception(self):
        assert issubclass(CurrencyError, Exception)
