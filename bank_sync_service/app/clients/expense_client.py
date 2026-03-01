from typing import Dict, Any

import httpx

from app.config import settings
from app.exceptions import TransactionLimitExceededError
from .base import BaseServiceClient


class ExpenseServiceClient(BaseServiceClient):
    def __init__(self):
        super().__init__(settings.EXPENSE_SERVICE_URL)

    async def create_expense(self, expense_data: Dict[str, Any], user_id: int, workspace_id: str) -> Dict[str, Any]:
        try:
            return await self.post(
                "/internal/",
                data=expense_data,
                params={"user_id": user_id, "workspace_id": workspace_id},
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise TransactionLimitExceededError("expense")
            raise
