"""API client for account_service (port 8009)."""
from __future__ import annotations

from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class AccountApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8009") -> None:
        super().__init__(base_url)

    async def create(self, name: str, currency: str = "USD", account_type: str = "checking", balance: float = 0) -> ApiResponse:
        resp = await self._post("/accounts/", json={"name": name, "currency": currency, "type": account_type, "balance": balance})
        return self._parse(resp)

    async def list_all(self) -> ApiResponse:
        resp = await self._get("/accounts/")
        return self._parse(resp)

    async def get(self, account_id: int) -> ApiResponse:
        resp = await self._get(f"/accounts/{account_id}")
        return self._parse(resp)

    async def update(self, account_id: int, **fields) -> ApiResponse:
        resp = await self._put(f"/accounts/{account_id}", json=fields)
        return self._parse(resp)

    async def archive(self, account_id: int) -> ApiResponse:
        resp = await self._patch(f"/accounts/{account_id}/archive")
        return self._parse(resp)

    async def summaries(self) -> ApiResponse:
        resp = await self._get("/accounts/summaries")
        return self._parse(resp)

    async def statistics(self) -> ApiResponse:
        resp = await self._get("/accounts/statistics")
        return self._parse(resp)

    async def summary(self, account_id: int) -> ApiResponse:
        resp = await self._get(f"/accounts/{account_id}/summary")
        return self._parse(resp)

    async def transactions(self, account_id: int) -> ApiResponse:
        resp = await self._get(f"/accounts/{account_id}/transactions")
        return self._parse(resp)
