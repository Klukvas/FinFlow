import httpx
from typing import Optional
from app.utils.logger import get_logger
from app.config import settings
from fastapi import HTTPException

class UserServiceClient:
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.timeout = 10.0
        self.logger = get_logger(__name__)
        
        # Create client with proper configuration
        self.client = httpx.Client(
            base_url=self.base_url, 
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )

    def get_user_base_currency(self, user_id: int) -> Optional[str]:
        """
        Get user's base currency from user service.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User's base currency code or None if unavailable
        """
        try:
            # Call internal endpoint to get user details
            response = self.client.get(
                f"/internal/users/{user_id}",
                headers={"X-Internal-Token": settings.INTERNAL_SECRET_TOKEN}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("base_currency", settings.DEFAULT_CURRENCY)
            else:
                self.logger.warning(f"Failed to fetch user currency: {response.status_code}")
                return settings.DEFAULT_CURRENCY  # Default to configured currency

        except Exception as e:
            self.logger.error(f"Error calling user service: {e}")
            return settings.DEFAULT_CURRENCY  # Default to configured currency

    def close(self):
        """Close HTTP client"""
        self.client.close()

