"""API client for recurring_service (port 8005)."""
from __future__ import annotations

from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class RecurringApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8005") -> None:
        super().__init__(base_url)

    async def create(self, **kwargs) -> ApiResponse:
        resp = await self._post("/recurring-payments/", json=kwargs)
        return self._parse(resp)

    async def list_all(self, **params) -> ApiResponse:
        resp = await self._get("/recurring-payments/", params=params or None)
        return self._parse(resp)

    async def get(self, payment_id: str) -> ApiResponse:
        resp = await self._get(f"/recurring-payments/{payment_id}")
        return self._parse(resp)

    async def update(self, payment_id: str, **fields) -> ApiResponse:
        resp = await self._put(f"/recurring-payments/{payment_id}", json=fields)
        return self._parse(resp)

    async def delete(self, payment_id: str) -> ApiResponse:
        resp = await self._delete(f"/recurring-payments/{payment_id}")
        return self._parse(resp)

    async def pause(self, payment_id: str) -> ApiResponse:
        resp = await self._post(f"/recurring-payments/{payment_id}/pause")
        return self._parse(resp)

    async def resume(self, payment_id: str) -> ApiResponse:
        resp = await self._post(f"/recurring-payments/{payment_id}/resume")
        return self._parse(resp)

    async def get_schedules(self, payment_id: str, **params) -> ApiResponse:
        resp = await self._get(
            f"/recurring-payments/{payment_id}/schedules", params=params or None
        )
        return self._parse(resp)

    async def get_statistics(self) -> ApiResponse:
        resp = await self._get("/recurring-payments/statistics/summary")
        return self._parse(resp)
