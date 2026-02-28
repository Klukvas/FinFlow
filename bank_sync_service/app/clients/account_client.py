from typing import Dict, Any, Optional

from app.config import settings
from .base import BaseServiceClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AccountServiceClient(BaseServiceClient):
    def __init__(self):
        super().__init__(settings.ACCOUNT_SERVICE_URL)

    async def get_account(self, account_id: int, user_id: int, workspace_id: str) -> Optional[Dict[str, Any]]:
        try:
            return await self.get(
                f"/internal/accounts/{account_id}",
                params={"user_id": user_id, "workspace_id": workspace_id},
            )
        except Exception as e:
            logger.warning(f"Failed to get account {account_id}: {str(e)}")
            return None
