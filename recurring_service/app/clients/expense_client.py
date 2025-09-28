from typing import Dict, Any, Optional
from uuid import UUID

from app.config import settings
from .base import BaseServiceClient


class ExpenseServiceClient(BaseServiceClient):
    """Клиент для взаимодействия с expense_service"""

    def __init__(self):
        super().__init__(settings.EXPENSE_SERVICE_URL)

    async def create_expense(self, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать новый расход"""
        return await self.post("/internal", data=expense_data)

    async def get_expense(self, expense_id: UUID) -> Dict[str, Any]:
        """Получить расход по ID"""
        return await self.get(f"/api/v1/expenses/{expense_id}")

    async def update_expense(self, expense_id: UUID, expense_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить расход"""
        return await self.put(f"/api/v1/expenses/{expense_id}", data=expense_data)

    async def delete_expense(self, expense_id: UUID) -> Dict[str, Any]:
        """Удалить расход"""
        return await self.delete(f"/api/v1/expenses/{expense_id}")

    async def get_expenses(
        self,
        user_id: Optional[str] = None,
        category_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        size: int = 50
    ) -> Dict[str, Any]:
        """Получить список расходов с фильтрацией"""
        params = {
            "page": page,
            "size": size
        }
        
        if user_id:
            params["user_id"] = user_id
        if category_id:
            params["category_id"] = category_id
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        return await self.get("/api/v1/expenses", params=params)
