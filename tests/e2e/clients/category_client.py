"""API client for category_service (port 8002)."""
from __future__ import annotations

from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class CategoryApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8002") -> None:
        super().__init__(base_url)

    async def create(self, name: str, parent_id: int | None = None, cat_type: str = "EXPENSE") -> ApiResponse:
        payload: dict = {"name": name, "type": cat_type.upper()}
        if parent_id is not None:
            payload["parent_id"] = parent_id
        resp = await self._post("/categories/", json=payload)
        return self._parse(resp)

    async def list_all(self, flat: bool = True) -> ApiResponse:
        resp = await self._get("/categories/", params={"flat": str(flat).lower()})
        return self._parse(resp)

    async def get(self, category_id: int) -> ApiResponse:
        resp = await self._get(f"/categories/{category_id}")
        return self._parse(resp)

    async def get_children(self, category_id: int) -> ApiResponse:
        resp = await self._get(f"/categories/{category_id}/children")
        return self._parse(resp)

    async def update(self, category_id: int, name: str) -> ApiResponse:
        resp = await self._put(f"/categories/{category_id}", json={"name": name})
        return self._parse(resp)

    async def delete(self, category_id: int) -> ApiResponse:
        resp = await self._delete(f"/categories/{category_id}")
        return self._parse(resp)

    async def statistics(self) -> ApiResponse:
        resp = await self._get("/categories/statistics")
        return self._parse(resp)

    async def create_from_mcc(self, mcc_code: str, language: str = "en") -> ApiResponse:
        resp = await self._post("/categories/from-mcc", json={"mcc_code": mcc_code, "language": language})
        return self._parse(resp)

    async def get_mcc_codes(self, language: str | None = None) -> ApiResponse:
        params = {"language": language} if language else None
        resp = await self._get("/mcc/codes", params=params)
        return self._parse(resp)
