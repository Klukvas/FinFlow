from __future__ import annotations

import httpx
from typing import Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class CurrencyServiceClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or settings.CURRENCY_SERVICE_URL.rstrip("/")
        self.client = httpx.Client(timeout=5.0)

    def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount or None if conversion fails
        """
        try:
            url = f"{self.base_url}/api/v1/convert"
            json_data = {
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency
            }
            
            resp = self.client.post(url, json=json_data)
            
            if resp.status_code == 200:
                data = resp.json()
                converted = data.get("converted_amount")
                rate = data.get("rate")
                logger.info(f"Currency conversion: {amount} {from_currency} = {converted} {to_currency} (rate: {rate})")
                return converted
            
            logger.error(f"Currency conversion failed: status={resp.status_code}, response={resp.text}")
            return None
        except Exception as e:
            logger.error(f"Currency conversion exception: {e}")
            return None

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Exchange rate or None if rate cannot be determined
        """
        try:
            url = f"{self.base_url}/api/v1/convert"
            json_data = {
                "amount": 1.0,  # Use 1.0 to get the rate
                "from_currency": from_currency,
                "to_currency": to_currency
            }
            
            resp = self.client.post(url, json=json_data)
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("rate")
            
            return None
        except Exception:
            return None

