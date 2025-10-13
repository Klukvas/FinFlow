from app.clients.base import BaseHttpClient
from app.config import settings
from app.utils.logger import get_logger
from typing import Dict, Any

class UserServiceClient(BaseHttpClient):
    def __init__(self):
        super().__init__(base_url=settings.USER_SERVICE_URL)
        self.logger = get_logger(__name__)

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get user information by ID.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Dict containing user information
            
        Raises:
            HTTPException: If user not found
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Internal-Secret": settings.INTERNAL_SECRET
            }
            
            response = await self.get(
                f"/internal/users/{user_id}",
                headers=headers
            )
            
            if response.status_code == 404:
                raise Exception("User not found")
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Error getting user {user_id}: {e}")
            raise
