from typing import Dict, Any

from app.config import settings
from .base import BaseServiceClient


class IncomeServiceClient(BaseServiceClient):
    def __init__(self):
        super().__init__(settings.INCOME_SERVICE_URL)

    async def create_income(self, income_data: Dict[str, Any], user_id: int, workspace_id: str) -> Dict[str, Any]:
        return await self.post(
            "/internal/",
            data=income_data,
            params={"user_id": user_id, "workspace_id": workspace_id},
        )
