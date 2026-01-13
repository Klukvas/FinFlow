"""
Client for communicating with the User Service.
"""
import httpx
from typing import Optional
from dataclasses import dataclass
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UserInfo:
    """User information returned from user service"""
    id: int
    email: str
    username: str
    base_currency: str
    default_workspace_id: Optional[str] = None


class UserClient:
    """HTTP client for User Service"""
    
    def __init__(self):
        self.base_url = settings.USER_SERVICE_URL
        self.timeout = 10.0
    
    def _get_headers(self) -> dict:
        """Get headers for internal service communication"""
        return {"X-Internal-Token": settings.INTERNAL_SECRET_TOKEN}
    
    def get_user(self, user_id: int) -> Optional[UserInfo]:
        """
        Get user information by ID.
        
        Args:
            user_id: The user ID to look up
            
        Returns:
            UserInfo or None if not found
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/internal/users/{user_id}",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return UserInfo(
                        id=data["id"],
                        email=data["email"],
                        username=data["username"],
                        base_currency=data["base_currency"],
                        default_workspace_id=data.get("default_workspace_id")
                    )
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
    
    def get_user_by_email(self, email: str) -> Optional[UserInfo]:
        """
        Get user information by email address.
        
        Args:
            email: The email address to look up
            
        Returns:
            UserInfo or None if not found
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                # URL encode the email for path parameter
                import urllib.parse
                encoded_email = urllib.parse.quote(email, safe='')
                
                response = client.get(
                    f"{self.base_url}/internal/users/by-email/{encoded_email}",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return UserInfo(
                        id=data["id"],
                        email=data["email"],
                        username=data["username"],
                        base_currency=data["base_currency"],
                        default_workspace_id=data.get("default_workspace_id")
                    )
                elif response.status_code == 404:
                    logger.debug(f"User with email {email} not found")
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
    
    def get_users_batch(self, user_ids: list[int]) -> dict[int, UserInfo]:
        """
        Get multiple users by their IDs.
        
        Args:
            user_ids: List of user IDs to look up
            
        Returns:
            Dict mapping user_id to UserInfo for found users
        """
        result = {}
        for user_id in user_ids:
            user = self.get_user(user_id)
            if user:
                result[user_id] = user
        return result

