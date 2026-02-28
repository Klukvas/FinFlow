from typing import Dict, Any, Optional

from app.config import settings
from .base import BaseServiceClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CategoryServiceClient(BaseServiceClient):
    def __init__(self):
        super().__init__(settings.CATEGORY_SERVICE_URL)

    async def get_category_by_mcc(self, mcc: int, user_id: int, workspace_id: str) -> Optional[Dict[str, Any]]:
        try:
            return await self.get(
                f"/internal/mcc/{mcc}",
                params={"user_id": user_id, "workspace_id": workspace_id},
            )
        except Exception as e:
            logger.warning(f"Failed to get category for MCC {mcc}: {str(e)}")
            return None
