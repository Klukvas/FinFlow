from typing import Dict, Any, Optional, List
from app.config import settings
from .base import BaseServiceClient


class CategoryServiceClient(BaseServiceClient):
    """Клиент для взаимодействия с category_service"""

    def __init__(self):
        super().__init__(settings.CATEGORY_SERVICE_URL)

    async def get_category(self, category_id: int, user_id: int) -> Dict[str, Any]:
        """Получить категорию по ID"""
        return await self.get(f"/internal/categories/{category_id}?user_id={user_id}")

    async def get_categories(
        self,
        user_id: Optional[str] = None,
        category_type: Optional[str] = None,
        parent_id: Optional[str] = None,
        page: int = 1,
        size: int = 50
    ) -> Dict[str, Any]:
        """Получить список категорий с фильтрацией"""
        params = {
            "page": page,
            "size": size
        }
        
        if user_id:
            params["user_id"] = user_id
        if category_type:
            params["type"] = category_type
        if parent_id:
            params["parent_id"] = parent_id

        return await self.get("/internal/categories", params=params)

    async def create_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать новую категорию"""
        return await self.post("/internal/categories", data=category_data)

    async def update_category(self, category_id: int, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить категорию"""
        return await self.put(f"/internal/categories/{category_id}", data=category_data)

    async def delete_category(self, category_id: int) -> Dict[str, Any]:
        """Удалить категорию"""
        return await self.delete(f"/internal/categories/{category_id}")

    async def validate_category_exists(self, category_id: int, user_id: int) -> bool:
        """Проверить существование категории"""
        try:
            await self.get_category(category_id, user_id)
            return True
        except Exception:
            return False
