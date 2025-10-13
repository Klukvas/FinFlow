import httpx
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

class CurrencyServiceClient:
    def __init__(self):
        self.base_url = settings.CURRENCY_SERVICE_URL
        self.http_client = httpx.AsyncClient(timeout=10.0)
        self.logger = logger

    async def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Convert amount from one currency to another using currency service.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount or None if conversion fails
        """
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/convert",
                json={
                    "amount": amount,
                    "from_currency": from_currency,
                    "to_currency": to_currency
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("converted_amount")
            else:
                self.logger.error(f"Currency conversion failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calling currency service: {e}")
            return None

    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Get exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Exchange rate or None if rate cannot be determined
        """
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/convert",
                json={
                    "amount": 1.0,  # Use 1.0 to get the rate
                    "from_currency": from_currency,
                    "to_currency": to_currency
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("rate")
            else:
                self.logger.error(f"Exchange rate fetch failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calling currency service: {e}")
            return None

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
