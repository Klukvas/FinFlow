from typing import Dict, Any

from app.config import settings
from .base import BaseServiceClient


class ExpenseServiceClient(BaseServiceClient):
    def __init__(self):
        super().__init__(settings.EXPENSE_SERVICE_URL)

    async def create_expense(self, expense_data: Dict[str, Any], user_id: int, workspace_id: str) -> Dict[str, Any]:
        return await self.post(
            "/internal/",
            data=expense_data,
            params={"user_id": user_id, "workspace_id": workspace_id},
        )
