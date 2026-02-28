"""API client for ai_assistant_service (port 8015)."""
from __future__ import annotations

from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class AiAssistantApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8015") -> None:
        super().__init__(base_url)

    async def get_prompts(self) -> ApiResponse:
        resp = await self._get("/api/v1/prompts")
        return self._parse(resp)

    async def analyze(self, prompt_id: str, language: str = "ru") -> ApiResponse:
        resp = await self._post(
            "/api/v1/analyze",
            json={"prompt_id": prompt_id, "language": language},
        )
        return self._parse(resp)

    async def get_result(self, prompt_id: str, language: str = "ru") -> ApiResponse:
        resp = await self._get(
            f"/api/v1/results/{prompt_id}",
            params={"language": language},
        )
        return self._parse(resp)

    async def get_usage(self) -> ApiResponse:
        resp = await self._get("/api/v1/usage")
        return self._parse(resp)
