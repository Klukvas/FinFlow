from app.clients.base import BaseHttpClient
from app.config import settings
from app.utils.logger import get_logger
from typing import Optional

logger = get_logger(__name__)

class CurrencyServiceClient(BaseHttpClient):
    def __init__(self):
        super().__init__(base_url=settings.CURRENCY_SERVICE_URL)
        self.logger = get_logger(__name__)

    async def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
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
            headers = {"Content-Type": "application/json"}
            json_data = {
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency
            }
            
            response = await self.post(url, headers=headers, json=json_data)
            
            if response.status_code == 200:
                data = response.json()
                converted = data.get("converted_amount")
                rate = data.get("rate")
                logger.info(f"Currency conversion: {amount} {from_currency} = {converted} {to_currency} (rate: {rate})")
                return converted
            
            logger.error(f"Currency conversion failed: status={response.status_code}, response={response.text}")
            return None
        except Exception as e:
            logger.error(f"Currency conversion exception: {e}")
            return None

    def get_user_base_currency(self, user_id: int) -> str:
        """
        Get user's base currency from user service.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            User's base currency code (e.g., 'USD', 'EUR'). Defaults to 'USD' on error.
        """
        try:
            # Use a synchronous client for this simple call
            import httpx
            
            url = f"{settings.USER_SERVICE_URL}/internal/users/{user_id}"
            headers = {"X-Internal-Token": settings.INTERNAL_SECRET_TOKEN}
            
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url, headers=headers)
                
                if resp.status_code == 200:
                    user_data = resp.json()
                    return user_data.get("base_currency", settings.DEFAULT_CURRENCY)

            # If user not found or any other error, return default
            return settings.DEFAULT_CURRENCY

        except Exception as e:
            logger.warning(f"Could not fetch user currency for user {user_id}: {e}")
            return settings.DEFAULT_CURRENCY

