"""API client for user_service (port 8001)."""
from __future__ import annotations

from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class UserApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8001") -> None:
        super().__init__(base_url)

    async def register(self, email: str, password: str, base_currency: str = "USD") -> ApiResponse:
        resp = await self._post("/auth/register", json={"email": email, "password": password, "base_currency": base_currency})
        return self._parse(resp)

    async def login(self, email: str, password: str) -> ApiResponse:
        resp = await self._post("/auth/login", json={"email": email, "password": password})
        return self._parse(resp)

    async def register_and_auth(self, email: str, password: str, base_currency: str = "USD") -> ApiResponse:
        result = await self.register(email, password, base_currency)
        if result.ok:
            self.set_token(result.data["access_token"])
        return result

    async def login_and_auth(self, email: str, password: str) -> ApiResponse:
        result = await self.login(email, password)
        if result.ok:
            self.set_token(result.data["access_token"])
        return result

    async def get_me(self) -> ApiResponse:
        resp = await self._get("/auth/me")
        return self._parse(resp)

    async def update_me(self, **fields) -> ApiResponse:
        resp = await self._put("/auth/me", json=fields)
        return self._parse(resp)

    async def change_password(self, current_password: str, new_password: str) -> ApiResponse:
        resp = await self._post("/auth/change-password", json={"current_password": current_password, "new_password": new_password})
        return self._parse(resp)

    async def refresh_token(self, refresh_token: str) -> ApiResponse:
        resp = await self._post("/auth/refresh", json={"refresh_token": refresh_token})
        return self._parse(resp)
