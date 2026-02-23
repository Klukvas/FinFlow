"""API client for income_service (port 8004)."""
from __future__ import annotations

from typing import Any
from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class IncomeApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8004") -> None:
        super().__init__(base_url)

    async def create(self, amount: float, **kwargs) -> ApiResponse:
        payload: dict[str, Any] = {"amount": amount, **kwargs}
        resp = await self._post("/incomes/", json=payload)
        return self._parse(resp)

    async def list_all(self) -> ApiResponse:
        resp = await self._get("/incomes/")
        return self._parse(resp)

    async def list_paginated(self, page: int = 1, size: int = 20) -> ApiResponse:
        resp = await self._get("/incomes/paginated", params={"page": page, "size": size})
        return self._parse(resp)

    async def get(self, income_id: int) -> ApiResponse:
        resp = await self._get(f"/incomes/{income_id}")
        return self._parse(resp)

    async def update(self, income_id: int, **fields) -> ApiResponse:
        resp = await self._put(f"/incomes/{income_id}", json=fields)
        return self._parse(resp)

    async def delete(self, income_id: int) -> ApiResponse:
        resp = await self._delete(f"/incomes/{income_id}")
        return self._parse(resp)

    async def by_category(self, category_id: int) -> ApiResponse:
        resp = await self._get(f"/incomes/category/{category_id}")
        return self._parse(resp)
