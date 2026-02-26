"""
Unified CurrencyServiceClient for currency conversion.

Replaces 5 per-service app/clients/currency_service_client.py files.
Provides both sync and async interfaces.
"""

import os
from typing import Optional

import httpx

from shared.logging import get_logger

logger = get_logger(__name__)


class CurrencyServiceClient:
    """Synchronous client for currency_service conversion API."""

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

    def close(self):
        self.client.close()


class AsyncCurrencyServiceClient:
    """Async client for currency_service conversion API."""

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

    async def close(self):
        await self.client.aclose()
