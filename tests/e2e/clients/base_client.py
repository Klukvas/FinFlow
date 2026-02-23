"""Base async HTTP client for all service clients."""
from __future__ import annotations

import httpx
from typing import Any, Optional
from uuid import UUID

from tests.e2e.models.responses import ApiResponse


class BaseApiClient:
    """Async HTTP client with token management and workspace header support."""

    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._token: Optional[str] = None
        self._workspace_id: Optional[str] = None

    def set_token(self, token: str) -> None:
        self._token = token

    def clear_token(self) -> None:
        self._token = None

    def set_workspace_id(self, workspace_id: str | UUID) -> None:
        self._workspace_id = str(workspace_id)

    def clear_workspace_id(self) -> None:
        self._workspace_id = None

    def _build_headers(self, extra: Optional[dict[str, str]] = None) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if self._workspace_id:
            headers["X-Workspace-Id"] = self._workspace_id
        if extra:
            headers.update(extra)
        return headers

    async def _get(
        self,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await client.get(
                f"{self._base_url}{path}",
                params=params,
                headers=self._build_headers(extra_headers),
            )

    async def _post(
        self,
        path: str,
        *,
        json: Optional[Any] = None,
        params: Optional[dict[str, Any]] = None,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await client.post(
                f"{self._base_url}{path}",
                json=json,
                params=params,
                headers=self._build_headers(extra_headers),
            )

    async def _put(
        self,
        path: str,
        *,
        json: Optional[Any] = None,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await client.put(
                f"{self._base_url}{path}",
                json=json,
                headers=self._build_headers(extra_headers),
            )

    async def _patch(
        self,
        path: str,
        *,
        json: Optional[Any] = None,
        params: Optional[dict[str, Any]] = None,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await client.patch(
                f"{self._base_url}{path}",
                json=json,
                params=params,
                headers=self._build_headers(extra_headers),
            )

    async def _delete(
        self,
        path: str,
        *,
        extra_headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await client.delete(
                f"{self._base_url}{path}",
                headers=self._build_headers(extra_headers),
            )

    @staticmethod
    def _parse(response: httpx.Response) -> ApiResponse:
        """Convert httpx.Response to ApiResponse."""
        try:
            body = response.json()
        except Exception:
            body = None

        if 200 <= response.status_code < 300:
            return ApiResponse(data=body, status_code=response.status_code, raw=body)

        error_msg = "Unknown error"
        if isinstance(body, dict):
            error_msg = (
                body.get("detail")
                or body.get("error")
                or body.get("message")
                or str(body)
            )
        elif isinstance(body, list) and body:
            error_msg = str(body)
        elif body is not None:
            error_msg = str(body)

        return ApiResponse(
            error=str(error_msg),
            status_code=response.status_code,
            raw=body if isinstance(body, dict) else {"raw": body},
        )

    async def health_check(self) -> bool:
        try:
            response = await self._get("/health")
            return response.status_code == 200
        except Exception:
            return False
