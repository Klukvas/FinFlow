"""API client for bank_sync_service (port 8016)."""
from __future__ import annotations

from typing import Any, Optional

from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class BankSyncApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8016") -> None:
        super().__init__(base_url)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health(self) -> ApiResponse:
        resp = await self._get("/health")
        return self._parse(resp)

    async def internal_health(self) -> ApiResponse:
        resp = await self._get("/internal/health")
        return self._parse(resp)

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    async def connect_bank(self, token: str) -> ApiResponse:
        resp = await self._post("/connections/", json={"token": token})
        return self._parse(resp)

    async def list_connections(self) -> ApiResponse:
        resp = await self._get("/connections/")
        return self._parse(resp)

    async def disconnect(self, connection_id: int) -> ApiResponse:
        resp = await self._delete(f"/connections/{connection_id}")
        return self._parse(resp)

    async def link_account(
        self,
        connection_id: int,
        linked_account_id: int,
        finflow_account_id: int,
    ) -> ApiResponse:
        resp = await self._put(
            f"/connections/{connection_id}/accounts/{linked_account_id}/link",
            json={"finflow_account_id": finflow_account_id},
        )
        return self._parse(resp)

    async def toggle_account_sync(
        self,
        connection_id: int,
        linked_account_id: int,
    ) -> ApiResponse:
        resp = await self._put(
            f"/connections/{connection_id}/accounts/{linked_account_id}/toggle",
        )
        return self._parse(resp)

    # ------------------------------------------------------------------
    # Sync operations
    # ------------------------------------------------------------------

    async def trigger_sync(
        self,
        connection_id: int,
        *,
        account_ids: Optional[list[int]] = None,
        days_back: int = 30,
    ) -> ApiResponse:
        payload: dict[str, Any] = {"days_back": days_back}
        if account_ids is not None:
            payload["account_ids"] = account_ids
        resp = await self._post(
            f"/connections/{connection_id}/sync",
            json=payload,
        )
        return self._parse(resp)

    async def preview_sync(
        self,
        connection_id: int,
        *,
        account_ids: Optional[list[int]] = None,
        days_back: int = 30,
    ) -> ApiResponse:
        payload: dict[str, Any] = {"days_back": days_back}
        if account_ids is not None:
            payload["account_ids"] = account_ids
        resp = await self._post(
            f"/connections/{connection_id}/sync/preview",
            json=payload,
        )
        return self._parse(resp)

    async def confirm_sync(
        self,
        connection_id: int,
        *,
        transactions: list[dict[str, Any]],
        days_back: int = 30,
    ) -> ApiResponse:
        resp = await self._post(
            f"/connections/{connection_id}/sync/confirm",
            json={"transactions": transactions, "days_back": days_back},
        )
        return self._parse(resp)

    async def get_sync_status(self, connection_id: int) -> ApiResponse:
        resp = await self._get(f"/connections/{connection_id}/sync/status")
        return self._parse(resp)

    async def get_sync_history(
        self,
        connection_id: int,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> ApiResponse:
        resp = await self._get(
            f"/connections/{connection_id}/sync/history",
            params={"skip": skip, "limit": limit},
        )
        return self._parse(resp)

    # ------------------------------------------------------------------
    # Webhook
    # ------------------------------------------------------------------

    async def webhook_verify(self) -> ApiResponse:
        resp = await self._get("/webhook/monobank")
        return self._parse(resp)

    async def webhook_receive(self, body: dict[str, Any]) -> ApiResponse:
        resp = await self._post("/webhook/monobank", json=body)
        return self._parse(resp)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def get_user_connections_internal(
        self,
        user_id: int,
        internal_token: str,
    ) -> ApiResponse:
        resp = await self._get(
            f"/internal/connections/user/{user_id}",
            extra_headers={"X-Internal-Token": internal_token},
        )
        return self._parse(resp)
