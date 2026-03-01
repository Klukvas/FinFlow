"""API client for goals_service (port 8006)."""
from __future__ import annotations

from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class GoalsApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8006") -> None:
        super().__init__(base_url)

    # ---- Goal CRUD ----

    async def create_goal(self, **kwargs) -> ApiResponse:
        resp = await self._post("/api/v1/goals/", json=kwargs)
        return self._parse(resp)

    async def list_goals(self, **params) -> ApiResponse:
        resp = await self._get("/api/v1/goals/", params=params or None)
        return self._parse(resp)

    async def get_goal(self, goal_id: int) -> ApiResponse:
        resp = await self._get(f"/api/v1/goals/{goal_id}")
        return self._parse(resp)

    async def update_goal(self, goal_id: int, **fields) -> ApiResponse:
        resp = await self._put(f"/api/v1/goals/{goal_id}", json=fields)
        return self._parse(resp)

    async def delete_goal(self, goal_id: int) -> ApiResponse:
        resp = await self._delete(f"/api/v1/goals/{goal_id}")
        return self._parse(resp)

    async def update_progress(self, goal_id: int, current_amount: float) -> ApiResponse:
        resp = await self._patch(
            f"/api/v1/goals/{goal_id}/progress",
            json={"current_amount": current_amount},
        )
        return self._parse(resp)

    async def get_statistics(self) -> ApiResponse:
        resp = await self._get("/api/v1/goals/statistics/overview")
        return self._parse(resp)

    # ---- Milestones ----

    async def create_milestone(self, goal_id: int, **kwargs) -> ApiResponse:
        resp = await self._post(f"/api/v1/goals/{goal_id}/milestones", json=kwargs)
        return self._parse(resp)

    async def list_milestones(self, goal_id: int) -> ApiResponse:
        resp = await self._get(f"/api/v1/goals/{goal_id}/milestones")
        return self._parse(resp)

    async def update_milestone_progress(
        self, goal_id: int, milestone_id: int, current_amount: float
    ) -> ApiResponse:
        resp = await self._patch(
            f"/api/v1/goals/{goal_id}/milestones/{milestone_id}/progress",
            json={"current_amount": current_amount},
        )
        return self._parse(resp)
