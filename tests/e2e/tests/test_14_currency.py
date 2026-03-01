"""E2E tests for currency service: supported currencies, rates, and conversion."""
import pytest

pytestmark = pytest.mark.currency


class TestCurrencyHealth:

    async def test_health_check(self, currency_client):
        result = await currency_client.get_health()
        data = result.raise_on_error()
        assert data["status"] in ("healthy", "degraded")


class TestSupportedCurrencies:

    async def test_get_supported_currencies(self, currency_client):
        result = await currency_client.get_supported_currencies()
        data = result.raise_on_error()
        assert "currencies" in data
        assert "total_count" in data
        assert data["total_count"] >= 1
        codes = [c["code"] for c in data["currencies"]]
        assert "USD" in codes

    async def test_currencies_have_required_fields(self, currency_client):
        data = (await currency_client.get_supported_currencies()).raise_on_error()
        for currency in data["currencies"]:
            assert "code" in currency
            assert "name" in currency


class TestCurrencyRates:

    async def test_get_rates_usd(self, currency_client):
        result = await currency_client.get_rates("USD")
        data = result.raise_on_error()
        assert "rates" in data
        assert isinstance(data["rates"], dict)
        assert len(data["rates"]) >= 1

    async def test_get_rates_eur(self, currency_client):
        result = await currency_client.get_rates("EUR")
        data = result.raise_on_error()
        assert "rates" in data


class TestCurrencyConversion:

    async def test_convert_usd_to_eur(self, currency_client):
        result = await currency_client.convert(100.0, "USD", "EUR")
        data = result.raise_on_error()
        assert "converted_amount" in data
        assert data["converted_amount"] > 0
        assert data["from_currency"] == "USD"
        assert data["to_currency"] == "EUR"

    async def test_convert_same_currency(self, currency_client):
        result = await currency_client.convert(100.0, "USD", "USD")
        data = result.raise_on_error()
        assert data["converted_amount"] == 100.0

    async def test_convert_zero_amount(self, currency_client):
        result = await currency_client.convert(0.0, "USD", "EUR")
        data = result.raise_on_error()
        assert data["converted_amount"] == 0.0

    async def test_convert_negative_amount(self, currency_client):
        result = await currency_client.convert(-100.0, "USD", "EUR")
        assert not result.ok

    async def test_convert_unsupported_currency(self, currency_client):
        result = await currency_client.convert(100.0, "USD", "XYZ")
        assert not result.ok
