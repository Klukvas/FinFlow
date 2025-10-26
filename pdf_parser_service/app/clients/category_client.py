import httpx
from typing import Optional, Dict, Any
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)

class CategoryServiceClient:
    """Client for interacting with category service"""
    
    def __init__(self):
        self.base_url = settings.category_service_url
        self.timeout = 30.0
        self.logger = logger
    
    async def get_mcc_category(self, mcc_code: int, language: str = "ru") -> Optional[Dict[str, Any]]:
        """
        Get MCC category information by MCC code
        
        Args:
            mcc_code: MCC code to look up
            language: Language for translation (ru, uk, en)
            
        Returns:
            Dict with category information or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get all MCC codes and find the one we need
                response = await client.get(
                    f"{self.base_url}/internal/mcc/codes",
                    params={"language": language},
                    headers={"X-Internal-Token": settings.internal_service_token}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    
                    # Find the MCC code in the response
                    for item in items:
                        if item.get("mcc_code") == mcc_code:
                            self.logger.info(f"Found MCC category for code {mcc_code}: {item.get('name')}")
                            return {
                                "mcc_code": item.get("mcc_code"),
                                "name": item.get("name"),
                                "translation": item.get("translation"),
                                "is_default": item.get("is_default")
                            }
                    
                    self.logger.warning(f"MCC code {mcc_code} not found in category service")
                    return None
                else:
                    self.logger.error(f"Failed to get MCC categories: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting MCC category for code {mcc_code}: {e}")
            return None
    
    async def get_default_categories(self, language: str = "ru") -> Optional[Dict[str, Any]]:
        """
        Get default MCC categories
        
        Args:
            language: Language for translation (ru, uk, en)
            
        Returns:
            Dict with default categories or None if error
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/internal/mcc/defaults",
                    params={"language": language},
                    headers={"X-Internal-Token": settings.internal_service_token}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.error(f"Failed to get default categories: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting default categories: {e}")
            return None
    
    async def check_category_exists(self, mcc_code: int, user_id: int) -> bool:
        """
        Check if user already has a category with the given MCC code
        
        Args:
            mcc_code: MCC code to check
            user_id: User ID to check
            
        Returns:
            bool: True if category exists, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/internal/categories/check-mcc/{mcc_code}",
                    params={"user_id": user_id},
                    headers={"X-Internal-Token": settings.internal_service_token}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    exists = data.get("exists", False)
                    self.logger.info(f"Category existence check for MCC {mcc_code}: {'exists' if exists else 'does not exist'}")
                    return exists
                else:
                    self.logger.error(f"Failed to check category existence: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error checking category existence for MCC {mcc_code}: {e}")
            return False

    async def get_category_by_mcc(self, mcc_code: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get category information by MCC code including category ID
        
        Args:
            mcc_code: MCC code to check
            user_id: User ID to check
            
        Returns:
            Dict with category information or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/internal/categories/get-by-mcc/{mcc_code}",
                    params={"user_id": user_id},
                    headers={"X-Internal-Token": settings.internal_service_token}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.logger.info(f"Category info for MCC {mcc_code}: {data}")
                    return data
                else:
                    self.logger.error(f"Failed to get category by MCC: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting category by MCC {mcc_code}: {e}")
            return None
