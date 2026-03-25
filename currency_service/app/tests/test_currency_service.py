"""
Unit tests for CurrencyService - business logic layer.
Tests service methods with mocked Redis and HTTP dependencies.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import redis as redis_lib
import httpx

from app.services.currency import CurrencyService
from app.schemas.currency import CurrencyInfo, ConversionResponse, CurrencyRatesResponse
from app.exceptions import (
    CurrencyCacheError,
    ExternalApiError,
)


# ---------------------------------------------------------------------------
# get_supported_currencies
# ---------------------------------------------------------------------------

class TestGetSupportedCurrencies:
    @pytest.mark.asyncio
    async def test_returns_cached_currencies(self, currency_service, mock_redis, sample_currencies):
        """When currencies are cached in Redis, return them without calling the API."""
        cached_data = json.dumps([c.model_dump() for c in sample_currencies])
        mock_redis.get.return_value = cached_data

        result = await currency_service.get_supported_currencies()

        assert len(result) == len(sample_currencies)
        assert all(isinstance(c, CurrencyInfo) for c in result)
        assert result[0].code == "USD"

    @pytest.mark.asyncio
    async def test_fetches_from_api_when_no_cache(self, currency_service, mock_redis, mock_http_client, sample_rates):
        """When cache is empty, fetch from API and return currencies."""
        mock_redis.get.return_value = None

        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": sample_rates}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = await currency_service.get_supported_currencies()

        assert len(result) > 0
        assert all(isinstance(c, CurrencyInfo) for c in result)
        # Should have cached the results
        mock_redis.setex.assert_called()

    @pytest.mark.asyncio
    async def test_returns_fallback_when_api_fails(self, currency_service, mock_redis, mock_http_client):
        """When both cache and API fail, return the hardcoded fallback list."""
        mock_redis.get.return_value = None
        mock_http_client.get.side_effect = Exception("API down")

        result = await currency_service.get_supported_currencies()

        assert len(result) > 0
        codes = {c.code for c in result}
        assert "USD" in codes
        assert "EUR" in codes

    @pytest.mark.asyncio
    async def test_returns_fallback_on_cache_error(self, currency_service, mock_redis, mock_http_client):
        """When Redis raises an error, fall back gracefully."""
        mock_redis.get.side_effect = redis_lib.RedisError("connection refused")

        result = await currency_service.get_supported_currencies()

        assert len(result) > 0
        assert all(isinstance(c, CurrencyInfo) for c in result)

    @pytest.mark.asyncio
    async def test_api_returns_empty_rates_uses_fallback(self, currency_service, mock_redis, mock_http_client):
        """When API returns empty rates, fall back to hardcoded list."""
        mock_redis.get.return_value = None

        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": {}}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = await currency_service.get_supported_currencies()

        # Empty rates means _fetch_currencies_from_api returns empty list,
        # which is falsy, so fallback is used
        assert len(result) > 0


# ---------------------------------------------------------------------------
# get_exchange_rate
# ---------------------------------------------------------------------------

class TestGetExchangeRate:
    @pytest.mark.asyncio
    async def test_same_currency_returns_one(self, currency_service):
        """Converting a currency to itself should return 1.0."""
        rate = await currency_service.get_exchange_rate("USD", "USD")
        assert rate == 1.0

    @pytest.mark.asyncio
    async def test_returns_cached_rate(self, currency_service, mock_redis, sample_rates):
        """When the rate is cached, return it from Redis."""
        cached_rates = json.dumps(sample_rates)
        mock_redis.get.return_value = cached_rates

        rate = await currency_service.get_exchange_rate("USD", "EUR")

        assert rate == 0.85

    @pytest.mark.asyncio
    async def test_fetches_rate_from_api(self, currency_service, mock_redis, mock_http_client, sample_rates):
        """When rate is not cached, fetch from API."""
        mock_redis.get.return_value = None

        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": sample_rates}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        rate = await currency_service.get_exchange_rate("USD", "EUR")

        assert rate == 0.85
        # Should cache the rate
        assert mock_redis.setex.call_count >= 1

    @pytest.mark.asyncio
    async def test_returns_none_when_api_fails_no_fallback(self, currency_service, mock_redis, mock_http_client):
        """When API fails and no fallback exists, return None."""
        mock_redis.get.return_value = None
        mock_http_client.get.side_effect = Exception("API unreachable")

        rate = await currency_service.get_exchange_rate("USD", "EUR")

        assert rate is None

    @pytest.mark.asyncio
    async def test_returns_fallback_rate_when_api_fails(self, currency_service, mock_redis, mock_http_client):
        """When API fails but fallback exists in Redis, return the fallback."""
        # First call (cache lookup for rates) returns None, triggering API call
        # API call fails, then fallback lookup succeeds
        def get_side_effect(key):
            if "fallback" in key:
                return "0.84"
            return None

        mock_redis.get.side_effect = get_side_effect
        mock_http_client.get.side_effect = Exception("API down")

        rate = await currency_service.get_exchange_rate("USD", "EUR")

        assert rate == 0.84

    @pytest.mark.asyncio
    async def test_unknown_target_currency_returns_none(self, currency_service, mock_redis, mock_http_client, sample_rates):
        """When the target currency is not in API rates and no fallback, return None."""
        mock_redis.get.return_value = None

        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": sample_rates}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        rate = await currency_service.get_exchange_rate("USD", "XYZ")

        assert rate is None


# ---------------------------------------------------------------------------
# convert_amount
# ---------------------------------------------------------------------------

class TestConvertAmount:
    @pytest.mark.asyncio
    async def test_same_currency_returns_same_amount(self, currency_service):
        """Converting same currency should return original amount with rate 1.0."""
        result = await currency_service.convert_amount(100.0, "USD", "USD")

        assert isinstance(result, ConversionResponse)
        assert result.amount == 100.0
        assert result.converted_amount == 100.0
        assert result.rate == 1.0
        assert result.from_currency == "USD"
        assert result.to_currency == "USD"

    @pytest.mark.asyncio
    async def test_converts_successfully(self, currency_service, mock_redis, sample_rates):
        """Successfully convert between two currencies."""
        cached_rates = json.dumps(sample_rates)
        mock_redis.get.return_value = cached_rates

        result = await currency_service.convert_amount(100.0, "USD", "EUR")

        assert isinstance(result, ConversionResponse)
        assert result.amount == 100.0
        assert result.converted_amount == 85.0  # 100 * 0.85
        assert result.rate == 0.85
        assert result.from_currency == "USD"
        assert result.to_currency == "EUR"

    @pytest.mark.asyncio
    async def test_returns_none_when_rate_unavailable(self, currency_service, mock_redis, mock_http_client):
        """When exchange rate is not available, return None."""
        mock_redis.get.return_value = None
        mock_http_client.get.side_effect = Exception("API down")

        result = await currency_service.convert_amount(100.0, "USD", "EUR")

        assert result is None

    @pytest.mark.asyncio
    async def test_converts_zero_amount(self, currency_service, mock_redis, sample_rates):
        """Zero amount should convert to zero."""
        cached_rates = json.dumps(sample_rates)
        mock_redis.get.return_value = cached_rates

        result = await currency_service.convert_amount(0.0, "USD", "EUR")

        assert result.converted_amount == 0.0

    @pytest.mark.asyncio
    async def test_conversion_rounds_to_two_decimals(self, currency_service, mock_redis):
        """Converted amount should be rounded to 2 decimal places."""
        rates = {"EUR": 0.8333}
        mock_redis.get.return_value = json.dumps(rates)

        result = await currency_service.convert_amount(100.0, "USD", "EUR")

        assert result.converted_amount == 83.33

    @pytest.mark.asyncio
    async def test_conversion_response_has_timestamp(self, currency_service):
        """Response should include a timestamp."""
        result = await currency_service.convert_amount(100.0, "USD", "USD")

        assert isinstance(result.timestamp, datetime)


# ---------------------------------------------------------------------------
# get_currency_rates
# ---------------------------------------------------------------------------

class TestGetCurrencyRates:
    @pytest.mark.asyncio
    async def test_returns_rates_response(self, currency_service, mock_redis, mock_http_client, sample_rates):
        """Successfully fetch and return currency rates."""
        mock_redis.get.return_value = None

        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": sample_rates}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = await currency_service.get_currency_rates("USD")

        assert isinstance(result, CurrencyRatesResponse)
        assert result.base_currency == "USD"
        assert result.rates == sample_rates

    @pytest.mark.asyncio
    async def test_returns_none_when_fetch_fails(self, currency_service, mock_redis, mock_http_client):
        """When API fetch fails, return None."""
        mock_redis.get.return_value = None
        mock_http_client.get.side_effect = Exception("API failure")

        result = await currency_service.get_currency_rates("USD")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_rates_for_non_usd_base(self, currency_service, mock_redis, mock_http_client):
        """Fetch rates for a non-USD base currency."""
        mock_redis.get.return_value = None
        eur_rates = {"USD": 1.18, "GBP": 0.86, "JPY": 130.0}

        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": eur_rates}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = await currency_service.get_currency_rates("EUR")

        assert result.base_currency == "EUR"
        assert result.rates["USD"] == 1.18


# ---------------------------------------------------------------------------
# _calculate_rate
# ---------------------------------------------------------------------------

class TestCalculateRate:
    def test_same_currency(self, currency_service):
        """Same from and to currency should return 1.0."""
        rates = {"EUR": 0.85, "GBP": 0.73}
        result = currency_service._calculate_rate(rates, "USD", "USD", "USD")
        assert result == 1.0

    def test_from_base_to_target(self, currency_service):
        """Rate from base currency to a target should return the direct rate."""
        rates = {"EUR": 0.85, "GBP": 0.73}
        result = currency_service._calculate_rate(rates, "USD", "USD", "EUR")
        assert result == 0.85

    def test_from_target_to_base(self, currency_service):
        """Rate from a non-base currency to the base should return inverted rate."""
        rates = {"EUR": 0.85, "GBP": 0.73}
        result = currency_service._calculate_rate(rates, "USD", "EUR", "USD")
        assert result == pytest.approx(1.0 / 0.85, rel=1e-6)

    def test_cross_rate_between_non_base_currencies(self, currency_service):
        """Rate between two non-base currencies is calculated via cross rate."""
        rates = {"EUR": 0.85, "GBP": 0.73}
        result = currency_service._calculate_rate(rates, "USD", "EUR", "GBP")
        expected = 0.73 / 0.85
        assert result == pytest.approx(expected, rel=1e-6)

    def test_unknown_target_returns_none(self, currency_service):
        """When target currency is not in rates, return None."""
        rates = {"EUR": 0.85}
        result = currency_service._calculate_rate(rates, "USD", "USD", "XYZ")
        assert result is None

    def test_unknown_from_currency_in_cross_rate_returns_none(self, currency_service):
        """When from_currency not in rates for cross rate, return None."""
        rates = {"GBP": 0.73}
        result = currency_service._calculate_rate(rates, "USD", "EUR", "GBP")
        assert result is None

    def test_zero_from_rate_returns_none(self, currency_service):
        """When from_rate is zero (division by zero risk), return None."""
        rates = {"EUR": 0.0, "GBP": 0.73}
        result = currency_service._calculate_rate(rates, "USD", "EUR", "GBP")
        assert result is None

    def test_zero_from_rate_to_base_returns_none(self, currency_service):
        """When converting to base with zero from_rate, return None."""
        rates = {"EUR": 0.0}
        result = currency_service._calculate_rate(rates, "USD", "EUR", "USD")
        assert result is None

    def test_negative_rates_handled(self, currency_service):
        """Negative rates (though unusual) should still compute, not crash."""
        rates = {"EUR": -0.5, "GBP": 0.73}
        # Negative from_rate is falsy check: -0.5 is truthy, so rate is computed
        result = currency_service._calculate_rate(rates, "USD", "USD", "EUR")
        assert result == -0.5


# ---------------------------------------------------------------------------
# _get_fallback_currencies
# ---------------------------------------------------------------------------

class TestGetFallbackCurrencies:
    def test_returns_popular_currencies(self, currency_service):
        """Fallback should return currencies matching popular_currencies set."""
        result = currency_service._get_fallback_currencies()

        codes = {c.code for c in result}
        assert "USD" in codes
        assert "EUR" in codes
        assert "UAH" in codes
        assert all(isinstance(c, CurrencyInfo) for c in result)

    def test_fallback_count_matches_popular(self, currency_service):
        """Fallback count should match popular currencies in supported_currencies."""
        result = currency_service._get_fallback_currencies()
        expected_count = len(
            currency_service.popular_currencies & set(currency_service.supported_currencies.keys())
        )
        assert len(result) == expected_count

    def test_fallback_has_all_required_fields(self, currency_service):
        """Each fallback currency should have all required fields populated."""
        result = currency_service._get_fallback_currencies()
        for c in result:
            assert c.code
            assert c.name
            assert c.symbol
            assert c.flag
            assert c.locale


# ---------------------------------------------------------------------------
# _fetch_exchange_rates
# ---------------------------------------------------------------------------

class TestFetchExchangeRates:
    @pytest.mark.asyncio
    async def test_successful_fetch(self, currency_service, mock_http_client, mock_redis, sample_rates):
        """Successful API fetch caches rates and returns them."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": sample_rates}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = await currency_service._fetch_exchange_rates("USD")

        assert result == sample_rates
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_status_error(self, currency_service, mock_http_client):
        """HTTP error should raise ExternalApiError."""
        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=mock_request, response=mock_response
        )
        mock_http_client.get.return_value = mock_response

        with pytest.raises(ExternalApiError):
            await currency_service._fetch_exchange_rates("USD")

    @pytest.mark.asyncio
    async def test_connection_error(self, currency_service, mock_http_client):
        """Connection error should raise ExternalApiError."""
        mock_http_client.get.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(ExternalApiError):
            await currency_service._fetch_exchange_rates("USD")


# ---------------------------------------------------------------------------
# _cache_rate / _get_cached_rate
# ---------------------------------------------------------------------------

class TestCacheOperations:
    @pytest.mark.asyncio
    async def test_cache_rate_success(self, currency_service, mock_redis):
        """Caching a rate should call setex on Redis."""
        await currency_service._cache_rate("USD", "EUR", 0.85)
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_rate_redis_error(self, currency_service, mock_redis):
        """Redis error during cache write should raise CurrencyCacheError."""
        mock_redis.setex.side_effect = redis_lib.RedisError("write failed")

        with pytest.raises(CurrencyCacheError):
            await currency_service._cache_rate("USD", "EUR", 0.85)

    @pytest.mark.asyncio
    async def test_get_cached_rate_returns_value(self, currency_service, mock_redis, sample_rates):
        """When cached rates exist, return the computed rate."""
        mock_redis.get.return_value = json.dumps(sample_rates)

        rate = await currency_service._get_cached_rate("USD", "EUR")

        assert rate == 0.85

    @pytest.mark.asyncio
    async def test_get_cached_rate_returns_none_on_miss(self, currency_service, mock_redis):
        """When no cached data, return None."""
        mock_redis.get.return_value = None

        rate = await currency_service._get_cached_rate("USD", "EUR")

        assert rate is None

    @pytest.mark.asyncio
    async def test_get_cached_rate_redis_error(self, currency_service, mock_redis):
        """Redis error during cache read should raise CurrencyCacheError."""
        mock_redis.get.side_effect = redis_lib.RedisError("read failed")

        with pytest.raises(CurrencyCacheError):
            await currency_service._get_cached_rate("USD", "EUR")


# ---------------------------------------------------------------------------
# _cache_fallback_rate / _get_fallback_rate
# ---------------------------------------------------------------------------

class TestFallbackRateCache:
    @pytest.mark.asyncio
    async def test_cache_fallback_rate(self, currency_service, mock_redis):
        """Fallback rate should be cached with longer TTL."""
        await currency_service._cache_fallback_rate("USD", "EUR", 0.85)
        mock_redis.setex.assert_called_once()
        # Verify it uses the fallback TTL (86400 seconds)
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 86400

    @pytest.mark.asyncio
    async def test_get_fallback_rate_returns_value(self, currency_service, mock_redis):
        """When fallback rate exists, return it as float."""
        mock_redis.get.return_value = "0.84"

        rate = await currency_service._get_fallback_rate("USD", "EUR")

        assert rate == 0.84

    @pytest.mark.asyncio
    async def test_get_fallback_rate_returns_none_on_miss(self, currency_service, mock_redis):
        """When no fallback cached, return None."""
        mock_redis.get.return_value = None

        rate = await currency_service._get_fallback_rate("USD", "EUR")

        assert rate is None

    @pytest.mark.asyncio
    async def test_cache_fallback_redis_error(self, currency_service, mock_redis):
        """Redis error during fallback cache write should raise CurrencyCacheError."""
        mock_redis.setex.side_effect = redis_lib.RedisError("write failed")

        with pytest.raises(CurrencyCacheError):
            await currency_service._cache_fallback_rate("USD", "EUR", 0.85)

    @pytest.mark.asyncio
    async def test_get_fallback_redis_error(self, currency_service, mock_redis):
        """Redis error during fallback read should raise CurrencyCacheError."""
        mock_redis.get.side_effect = redis_lib.RedisError("read failed")

        with pytest.raises(CurrencyCacheError):
            await currency_service._get_fallback_rate("USD", "EUR")


# ---------------------------------------------------------------------------
# _cache_currencies / _get_cached_currencies
# ---------------------------------------------------------------------------

class TestCurrenciesCache:
    @pytest.mark.asyncio
    async def test_cache_currencies(self, currency_service, mock_redis, sample_currencies):
        """Caching currencies should serialize and store in Redis."""
        cache_key = "currency:currencies_top10"
        await currency_service._cache_currencies(sample_currencies, cache_key)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        # TTL should be 86400 (24 hours)
        assert call_args[0][1] == 86400
        # Data should be valid JSON
        stored_data = json.loads(call_args[0][2])
        assert len(stored_data) == len(sample_currencies)

    @pytest.mark.asyncio
    async def test_get_cached_currencies(self, currency_service, mock_redis, sample_currencies):
        """Retrieving cached currencies should deserialize correctly."""
        cached_data = json.dumps([c.model_dump() for c in sample_currencies])
        mock_redis.get.return_value = cached_data

        result = await currency_service._get_cached_currencies("currency:currencies_top10")

        assert len(result) == len(sample_currencies)
        assert result[0].code == "USD"

    @pytest.mark.asyncio
    async def test_get_cached_currencies_miss(self, currency_service, mock_redis):
        """Cache miss should return None."""
        mock_redis.get.return_value = None

        result = await currency_service._get_cached_currencies("currency:currencies_top10")

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_currencies_redis_error(self, currency_service, mock_redis, sample_currencies):
        """Redis error during currencies cache write should raise CurrencyCacheError."""
        mock_redis.setex.side_effect = redis_lib.RedisError("write failed")

        with pytest.raises(CurrencyCacheError):
            await currency_service._cache_currencies(sample_currencies, "currency:test")

    @pytest.mark.asyncio
    async def test_get_cached_currencies_redis_error(self, currency_service, mock_redis):
        """Redis error during currencies read should raise CurrencyCacheError."""
        mock_redis.get.side_effect = redis_lib.RedisError("read failed")

        with pytest.raises(CurrencyCacheError):
            await currency_service._get_cached_currencies("currency:test")


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_all_healthy(self, currency_service, mock_redis, mock_http_client):
        """When both Redis and API are accessible, return both as True."""
        mock_redis.ping.return_value = True
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_http_client.get.return_value = mock_response

        result = await currency_service.health_check()

        assert result["redis_connected"] is True
        assert result["api_accessible"] is True

    @pytest.mark.asyncio
    async def test_redis_down(self, currency_service, mock_redis, mock_http_client):
        """When Redis is unreachable, redis_connected should be False."""
        mock_redis.ping.side_effect = redis_lib.RedisError("connection refused")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_http_client.get.return_value = mock_response

        result = await currency_service.health_check()

        assert result["redis_connected"] is False
        assert result["api_accessible"] is True

    @pytest.mark.asyncio
    async def test_api_down(self, currency_service, mock_redis, mock_http_client):
        """When external API is unreachable, api_accessible should be False."""
        mock_redis.ping.return_value = True
        mock_http_client.get.side_effect = Exception("API timeout")

        result = await currency_service.health_check()

        assert result["redis_connected"] is True
        assert result["api_accessible"] is False

    @pytest.mark.asyncio
    async def test_api_non_200_status(self, currency_service, mock_redis, mock_http_client):
        """When API returns non-200 status, api_accessible should be False."""
        mock_redis.ping.return_value = True
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_http_client.get.return_value = mock_response

        result = await currency_service.health_check()

        assert result["redis_connected"] is True
        assert result["api_accessible"] is False

    @pytest.mark.asyncio
    async def test_both_down(self, currency_service, mock_redis, mock_http_client):
        """When both services are down, both should be False."""
        mock_redis.ping.side_effect = redis_lib.RedisError("connection refused")
        mock_http_client.get.side_effect = Exception("API timeout")

        result = await currency_service.health_check()

        assert result["redis_connected"] is False
        assert result["api_accessible"] is False


# ---------------------------------------------------------------------------
# _fetch_currencies_from_api
# ---------------------------------------------------------------------------

class TestFetchCurrenciesFromApi:
    @pytest.mark.asyncio
    async def test_successful_fetch(self, currency_service, mock_http_client, mock_redis, sample_rates):
        """Successfully fetch currencies from external API."""
        mock_redis.get.return_value = None

        mock_response = MagicMock()
        mock_response.json.return_value = {"rates": sample_rates}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.get.return_value = mock_response

        result = await currency_service._fetch_currencies_from_api()

        assert result is not None
        assert len(result) > 0
        codes = {c.code for c in result}
        # All returned currencies should be in popular_currencies
        assert codes.issubset(currency_service.popular_currencies)

    @pytest.mark.asyncio
    async def test_returns_none_on_failure(self, currency_service, mock_http_client, mock_redis):
        """When API fails, return None."""
        mock_redis.get.return_value = None
        mock_http_client.get.side_effect = Exception("API error")

        result = await currency_service._fetch_currencies_from_api()

        assert result is None


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------

class TestClose:
    @pytest.mark.asyncio
    async def test_closes_http_client(self, currency_service, mock_http_client):
        """Closing the service should close the HTTP client."""
        await currency_service.close()
        mock_http_client.aclose.assert_called_once()
