"""API client for subscription_service (port 8011)."""
from __future__ import annotations

from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class SubscriptionApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8011") -> None:
        super().__init__(base_url)

    async def list_plans(self) -> ApiResponse:
        resp = await self._get("/v1/plans")
        return self._parse(resp)

    async def list_plans_with_features(self) -> ApiResponse:
        resp = await self._get("/v1/plans/with-features")
        return self._parse(resp)

    async def get_subscription(self, user_id: int) -> ApiResponse:
        resp = await self._get(f"/v1/subscriptions/{user_id}")
        return self._parse(resp)

    async def get_entitlements(self, user_id: int) -> ApiResponse:
        resp = await self._get(f"/v1/entitlements/{user_id}")
        return self._parse(resp)

    async def get_user_features(self, user_id: int) -> ApiResponse:
        resp = await self._get(f"/v1/features/{user_id}")
        return self._parse(resp)

    async def set_plan(
        self, user_id: int, plan_code: str, internal_token: str | None = None
    ) -> ApiResponse:
        extra = {"X-Internal-Token": internal_token} if internal_token else None
        resp = await self._post(
            f"/v1/subscriptions/{user_id}:set_plan",
            json={"plan_code": plan_code},
            extra_headers=extra,
        )
        return self._parse(resp)

    async def cancel_subscription(self, user_id: int) -> ApiResponse:
        resp = await self._post(f"/v1/subscriptions/{user_id}:cancel")
        return self._parse(resp)

    async def list_features(self) -> ApiResponse:
        resp = await self._get("/v1/features")
        return self._parse(resp)

    async def get_plan_features(self, plan_code: str) -> ApiResponse:
        resp = await self._get(f"/v1/plans/{plan_code}/features")
        return self._parse(resp)
