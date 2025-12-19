"""
Client for communicating with the User Service.
"""
import httpx
from typing import Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserClient:
    """HTTP client for User Service"""
    
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.timeout = 10.0
    
    def get_user(self, user_id: int) -> Optional[dict]:
        """
        Get user information by ID.
        
        Args:
            user_id: The user ID to look up
            
        Returns:
            User data dict or None if not found
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/internal/users/{user_id}",
                    headers={"Authorization": f"Bearer {settings.INTERNAL_SECRET_TOKEN}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(
                        f"Unexpected response from user service: {response.status_code}"
                    )
                    return None
                    
        except httpx.RequestError as e:
            logger.error(f"Error communicating with user service: {e}")
            return None
    
    def user_exists(self, user_id: int) -> bool:
        """
        Check if a user exists.
        
        Args:
            user_id: The user ID to check
            
        Returns:
            True if user exists, False otherwise
        """
        return self.get_user(user_id) is not None

