"""API client for currency_service (port 8010)."""
from __future__ import annotations

from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class CurrencyApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8010") -> None:
        super().__init__(base_url)

    async def get_supported_currencies(self) -> ApiResponse:
        resp = await self._get("/api/v1/currencies")
        return self._parse(resp)

    async def get_rates(self, base_currency: str = "USD") -> ApiResponse:
        resp = await self._get("/api/v1/rates", params={"base_currency": base_currency})
        return self._parse(resp)

    async def convert(
        self, amount: float, from_currency: str, to_currency: str
    ) -> ApiResponse:
        resp = await self._post(
            "/api/v1/convert",
            json={
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
            },
        )
        return self._parse(resp)

    async def get_health(self) -> ApiResponse:
        resp = await self._get("/api/v1/health")
        return self._parse(resp)
