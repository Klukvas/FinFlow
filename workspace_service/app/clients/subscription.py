"""Subscription Service Client for checking limits"""
import httpx
from typing import Optional, Dict, Any
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionClient:
    """Client for communicating with subscription_service for limit checks"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.SUBSCRIPTION_SERVICE_URL).rstrip("/")
        self.internal_token = settings.INTERNAL_SECRET_TOKEN
        self.timeout = 5.0

    def _get_headers(self) -> dict:
        """Get headers for internal API calls"""
        headers = {"Content-Type": "application/json"}
        if self.internal_token:
            headers["X-Internal-Token"] = self.internal_token
        return headers

    def get_user_features(self, user_id: int) -> Dict[str, Any]:
        """Get user's feature entitlements"""
        try:
            url = f"{self.base_url}/v1/internal/features/{user_id}"
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self._get_headers())
                
                if response.status_code == 200:
                    features = response.json()
                    # Convert list to dict for easier lookup
                    return {f["feature_code"]: f for f in features}
                    
            logger.warning(
                f"Failed to get features for user {user_id}: status={response.status_code}"
            )
            return {}
            
        except httpx.TimeoutException:
            logger.error(f"Timeout getting features for user {user_id}")
            return {}
        except Exception as e:
            logger.error(f"Error getting features for user {user_id}: {e}")
            return {}

    def check_workspace_limit(self, user_id: int, current_count: int) -> bool:
        """Check if user can create more workspaces"""
        features = self.get_user_features(user_id)
        workspace_feature = features.get("workspaces", {})
        
        # If feature doesn't exist or is disabled, deny by default
        # (fail-closed: do not allow when subscription service is unreachable)
        if not workspace_feature:
            logger.warning(f"No workspace feature found for user {user_id}, denying by default")
            return False
            
        if not workspace_feature.get("enabled", False):
            logger.warning(f"Workspace feature disabled for user {user_id}")
            return False
            
        limit = workspace_feature.get("limit_value")
        if limit is None:
            return True  # Unlimited
            
        can_create = current_count < limit
        
        if not can_create:
            logger.info(
                f"User {user_id} reached workspace limit: {current_count}/{limit}"
            )
            
        return can_create

    def get_workspace_limit(self, user_id: int) -> Optional[int]:
        """Get user's workspace limit"""
        features = self.get_user_features(user_id)
        workspace_feature = features.get("workspaces", {})
        
        if not workspace_feature.get("enabled", False):
            return 0
            
        return workspace_feature.get("limit_value")

