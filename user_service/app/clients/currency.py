from __future__ import annotations

import httpx
from typing import Optional, List, Dict
from app.config import settings


class CurrencyClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or settings.CURRENCY_SERVICE_URL.rstrip("/")
        self.client = httpx.Client(timeout=5.0)

    def validate_currency(self, currency_code: str) -> bool:
        """
        Validate if a currency code is supported.
        
        Args:
            currency_code: The currency code to validate (e.g., 'USD', 'EUR')
            
        Returns:
            True if currency is supported, False otherwise
        """
        try:
            # Get the base URL without trailing slash
            base = self.base_url.rstrip("/")
            url = f"{base}/api/v1/currencies"
            
            resp = self.client.get(url)
            
            if resp.status_code == 200:
                data = resp.json()
                supported_currencies = data.get("currencies", [])
                
                # Check if the currency code is in the supported list
                return any(curr.get("code") == currency_code for curr in supported_currencies)
            
            # If we can't fetch the list, return False
            return False
            
        except Exception:
            # If the service is unavailable, allow the currency anyway
            # We don't want to block registration if the currency service is down
            return False
    
    def get_supported_currencies(self) -> List[Dict]:
        """Get list of supported currencies"""
        try:
            base = self.base_url.rstrip("/")
            url = f"{base}/api/v1/currencies"
            resp = self.client.get(url)
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("currencies", [])
            
            return []
        except Exception:
            return []

