from typing import Dict, Any, Optional
from uuid import UUID

from app.config import settings
from .base import BaseServiceClient


class IncomeServiceClient(BaseServiceClient):
    """Клиент для взаимодействия с income_service"""

    def __init__(self):
        super().__init__(settings.INCOME_SERVICE_URL)

    async def create_income(self, income_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать новый доход"""
        return await self.post("/api/v1/incomes", data=income_data)

    async def get_income(self, income_id: UUID) -> Dict[str, Any]:
        """Получить доход по ID"""
        return await self.get(f"/api/v1/incomes/{income_id}")

    async def update_income(self, income_id: UUID, income_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить доход"""
        return await self.put(f"/api/v1/incomes/{income_id}", data=income_data)

    async def delete_income(self, income_id: UUID) -> Dict[str, Any]:
        """Удалить доход"""
        return await self.delete(f"/api/v1/incomes/{income_id}")

    async def get_incomes(
        self,
        user_id: Optional[str] = None,
        category_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        size: int = 50
    ) -> Dict[str, Any]:
        """Получить список доходов с фильтрацией"""
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

        return await self.get("/api/v1/incomes", params=params)
