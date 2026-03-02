"""
Unified CurrencyServiceClient for currency conversion.

Replaces 5 per-service app/clients/currency_service_client.py files.
Provides both sync and async interfaces.
"""

import os
from typing import Dict, Optional

import httpx

from shared.logging import get_logger

logger = get_logger(__name__)

_sync_instance: Optional["CurrencyServiceClient"] = None
_async_instance: Optional["AsyncCurrencyServiceClient"] = None


class CurrencyServiceClient:
    """Synchronous client for currency_service conversion API."""

    @classmethod
    def get_instance(cls) -> "CurrencyServiceClient":
        global _sync_instance
        if _sync_instance is None:
            _sync_instance = cls()
        return _sync_instance

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.environ.get("CURRENCY_SERVICE_URL", "http://currency_service:8000")
        self.client = httpx.Client(timeout=10.0)

    def convert_amount(
        self, amount: float, from_currency: str, to_currency: str
    ) -> Optional[float]:
        """Convert amount between currencies. Returns None on failure."""
        if from_currency == to_currency:
            return amount
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/convert",
                json={
                    "amount": amount,
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("converted_amount")
            logger.error(f"Currency conversion failed: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error calling currency service: {e}")
            return None

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate between two currencies. Returns None on failure."""
        if from_currency == to_currency:
            return 1.0
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/convert",
                json={
                    "amount": 1.0,
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("rate")
            logger.error(f"Exchange rate fetch failed: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error calling currency service: {e}")
            return None

    def get_rates(self, base_currency: str) -> Optional[Dict[str, float]]:
        """Fetch all exchange rates for a base currency in one call."""
        try:
            response = self.client.get(
                f"{self.base_url}/api/v1/rates",
                params={"base_currency": base_currency},
            )
            if response.status_code == 200:
                return response.json().get("rates", {})
            logger.error(f"Rates fetch failed: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error fetching rates: {e}")
            return None

    @staticmethod
    def convert_with_rates(
        amount: float, from_currency: str, to_currency: str, rates: Dict[str, float]
    ) -> Optional[float]:
        """Convert amount using a pre-fetched rates dict (base_currency-relative)."""
        if from_currency == to_currency:
            return amount
        from_rate = rates.get(from_currency)
        to_rate = rates.get(to_currency)
        if from_rate and to_rate:
            return round(amount * (to_rate / from_rate), 2)
        return None

    def close(self):
        self.client.close()


class AsyncCurrencyServiceClient:
    """Async client for currency_service conversion API."""

    @classmethod
    def get_instance(cls) -> "AsyncCurrencyServiceClient":
        global _async_instance
        if _async_instance is None:
            _async_instance = cls()
        return _async_instance

    def __init__(self):
        self.base_url = os.environ.get("CURRENCY_SERVICE_URL", "http://currency_service:8000")
        self.client = httpx.AsyncClient(timeout=10.0)

    async def convert_amount(
        self, amount: float, from_currency: str, to_currency: str
    ) -> Optional[float]:
        """Convert amount between currencies. Returns None on failure."""
        if from_currency == to_currency:
            return amount
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/convert",
                json={
                    "amount": amount,
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("converted_amount")
            logger.error(f"Currency conversion failed: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error calling currency service: {e}")
            return None

    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate between two currencies. Returns None on failure."""
        if from_currency == to_currency:
            return 1.0
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/convert",
                json={
                    "amount": 1.0,
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("rate")
            logger.error(f"Exchange rate fetch failed: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error calling currency service: {e}")
            return None

    async def get_rates(self, base_currency: str) -> Optional[Dict[str, float]]:
        """Fetch all exchange rates for a base currency in one call."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/rates",
                params={"base_currency": base_currency},
            )
            if response.status_code == 200:
                return response.json().get("rates", {})
            logger.error(f"Rates fetch failed: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error fetching rates: {e}")
            return None

    @staticmethod
    def convert_with_rates(
        amount: float, from_currency: str, to_currency: str, rates: Dict[str, float]
    ) -> Optional[float]:
        """Convert amount using a pre-fetched rates dict (base_currency-relative)."""
        if from_currency == to_currency:
            return amount
        from_rate = rates.get(from_currency)
        to_rate = rates.get(to_currency)
        if from_rate and to_rate:
            return round(amount * (to_rate / from_rate), 2)
        return None

    async def close(self):
        await self.client.aclose()
