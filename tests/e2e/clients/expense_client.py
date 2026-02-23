"""API client for expense_service (port 8003)."""
from __future__ import annotations

from typing import Any, Optional
from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class ExpenseApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8003") -> None:
        super().__init__(base_url)

    async def create(self, amount: float, **kwargs) -> ApiResponse:
        payload: dict[str, Any] = {"amount": amount, **kwargs}
        resp = await self._post("/expenses/", json=payload)
        return self._parse(resp)

    async def list_all(self) -> ApiResponse:
        resp = await self._get("/expenses/")
        return self._parse(resp)

    async def list_paginated(self, page: int = 1, size: int = 20) -> ApiResponse:
        resp = await self._get("/expenses/paginated", params={"page": page, "size": size})
        return self._parse(resp)

    async def get(self, expense_id: int) -> ApiResponse:
        resp = await self._get(f"/expenses/{expense_id}")
        return self._parse(resp)

    async def update(self, expense_id: int, **fields) -> ApiResponse:
        resp = await self._patch(f"/expenses/{expense_id}", json=fields)
        return self._parse(resp)

    async def delete(self, expense_id: int) -> ApiResponse:
        resp = await self._delete(f"/expenses/{expense_id}")
        return self._parse(resp)

    async def by_category(self, category_id: int) -> ApiResponse:
        resp = await self._get(f"/expenses/category/{category_id}")
        return self._parse(resp)

    async def by_date_range(self, start_date: str, end_date: str) -> ApiResponse:
        resp = await self._get("/expenses/date-range/", params={"start_date": start_date, "end_date": end_date})
        return self._parse(resp)

    async def current_month_count(self) -> ApiResponse:
        resp = await self._get("/expenses/current-month-count")
        return self._parse(resp)
