"""API client for debt_service (port 8008)."""
from __future__ import annotations

from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class DebtApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8008") -> None:
        super().__init__(base_url)

    # ---- Debt CRUD ----

    async def create_debt(self, **kwargs) -> ApiResponse:
        resp = await self._post("/debts/", json=kwargs)
        return self._parse(resp)

    async def list_debts(
        self,
        *,
        active_only: bool = False,
        paid_off_only: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> ApiResponse:
        resp = await self._get(
            "/debts/",
            params={
                "active_only": str(active_only).lower(),
                "paid_off_only": str(paid_off_only).lower(),
                "skip": skip,
                "limit": limit,
            },
        )
        return self._parse(resp)

    async def get_debt(self, debt_id: int) -> ApiResponse:
        resp = await self._get(f"/debts/{debt_id}")
        return self._parse(resp)

    async def update_debt(self, debt_id: int, **fields) -> ApiResponse:
        resp = await self._put(f"/debts/{debt_id}", json=fields)
        return self._parse(resp)

    async def delete_debt(self, debt_id: int) -> ApiResponse:
        resp = await self._delete(f"/debts/{debt_id}")
        return self._parse(resp)

    async def get_summary(self) -> ApiResponse:
        resp = await self._get("/debts/summary/")
        return self._parse(resp)

    # ---- Payments ----

    async def create_payment(self, debt_id: int, **kwargs) -> ApiResponse:
        resp = await self._post(f"/debts/{debt_id}/payments/", json=kwargs)
        return self._parse(resp)

    async def list_payments(self, debt_id: int) -> ApiResponse:
        resp = await self._get(f"/debts/{debt_id}/payments/")
        return self._parse(resp)

    # ---- Contacts ----

    async def create_contact(self, **kwargs) -> ApiResponse:
        resp = await self._post("/contacts/", json=kwargs)
        return self._parse(resp)

    async def list_contacts(self) -> ApiResponse:
        resp = await self._get("/contacts/")
        return self._parse(resp)

    async def get_contact(self, contact_id: int) -> ApiResponse:
        resp = await self._get(f"/contacts/{contact_id}")
        return self._parse(resp)

    async def update_contact(self, contact_id: int, **fields) -> ApiResponse:
        resp = await self._put(f"/contacts/{contact_id}", json=fields)
        return self._parse(resp)

    async def delete_contact(self, contact_id: int) -> ApiResponse:
        resp = await self._delete(f"/contacts/{contact_id}")
        return self._parse(resp)
