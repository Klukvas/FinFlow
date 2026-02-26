from __future__ import annotations

import httpx
from typing import Optional
from app.config import settings


class UserServiceClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or settings.USER_SERVICE_URL.rstrip("/")
        self.client = httpx.Client(timeout=5.0)

    def get_user_base_currency(self, user_id: int) -> str:
        """
        Get user's base currency from user service.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            User's base currency code (e.g., 'USD', 'EUR'). Defaults to 'USD' on error.
        """
        try:
            url = f"{self.base_url}/internal/users/{user_id}"
            headers = {"X-Internal-Token": settings.INTERNAL_SECRET_TOKEN}
            
            resp = self.client.get(url, headers=headers)
            
            if resp.status_code == 200:
                user_data = resp.json()
                return user_data.get("base_currency", settings.DEFAULT_CURRENCY)

            # If user not found or any other error, return default
            return settings.DEFAULT_CURRENCY

        except (httpx.HTTPError, httpx.TimeoutException, Exception):
            # Return default currency on any error
            return settings.DEFAULT_CURRENCY

