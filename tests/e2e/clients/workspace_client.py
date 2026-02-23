"""API client for workspace_service (port 8012)."""
from __future__ import annotations

from uuid import UUID
from tests.e2e.clients.base_client import BaseApiClient
from tests.e2e.models.responses import ApiResponse


class WorkspaceApiClient(BaseApiClient):

    def __init__(self, base_url: str = "http://localhost:8012") -> None:
        super().__init__(base_url)

    # Workspace CRUD
    async def create(self, name: str, ws_type: str = "shared") -> ApiResponse:
        resp = await self._post("/workspaces", json={"name": name, "type": ws_type})
        return self._parse(resp)

    async def list_all(self, include_archived: bool = False) -> ApiResponse:
        resp = await self._get("/workspaces", params={"include_archived": str(include_archived).lower()})
        return self._parse(resp)

    async def get(self, workspace_id: str | UUID) -> ApiResponse:
        resp = await self._get(f"/workspaces/{workspace_id}")
        return self._parse(resp)

    async def update(self, workspace_id: str | UUID, name: str) -> ApiResponse:
        resp = await self._patch(f"/workspaces/{workspace_id}", json={"name": name})
        return self._parse(resp)

    async def archive(self, workspace_id: str | UUID) -> ApiResponse:
        resp = await self._post(f"/workspaces/{workspace_id}:archive")
        return self._parse(resp)

    async def unarchive(self, workspace_id: str | UUID) -> ApiResponse:
        resp = await self._post(f"/workspaces/{workspace_id}:unarchive")
        return self._parse(resp)

    async def leave(self, workspace_id: str | UUID) -> ApiResponse:
        resp = await self._post(f"/workspaces/{workspace_id}:leave")
        return self._parse(resp)

    async def transfer_ownership(self, workspace_id: str | UUID, new_owner_id: int) -> ApiResponse:
        resp = await self._post(f"/workspaces/{workspace_id}/owner:transfer", params={"new_owner_id": new_owner_id})
        return self._parse(resp)

    # Members
    async def list_members(self, workspace_id: str | UUID) -> ApiResponse:
        resp = await self._get(f"/workspaces/{workspace_id}/members")
        return self._parse(resp)

    async def update_member_role(self, workspace_id: str | UUID, user_id: int, role: str) -> ApiResponse:
        resp = await self._patch(f"/workspaces/{workspace_id}/members/{user_id}", json={"role": role})
        return self._parse(resp)

    async def remove_member(self, workspace_id: str | UUID, user_id: int) -> ApiResponse:
        resp = await self._delete(f"/workspaces/{workspace_id}/members/{user_id}")
        return self._parse(resp)

    # Invites (owner side)
    async def create_invite(self, workspace_id: str | UUID, email: str, role: str = "read") -> ApiResponse:
        resp = await self._post(f"/workspaces/{workspace_id}/invites", json={"email": email, "role": role})
        return self._parse(resp)

    async def list_invites(self, workspace_id: str | UUID) -> ApiResponse:
        resp = await self._get(f"/workspaces/{workspace_id}/invites")
        return self._parse(resp)

    async def cancel_invite(self, workspace_id: str | UUID, invite_id: str | UUID) -> ApiResponse:
        resp = await self._delete(f"/workspaces/{workspace_id}/invites/{invite_id}")
        return self._parse(resp)

    # My Invites (invitee side)
    async def list_my_invites(self) -> ApiResponse:
        resp = await self._get("/me/invites")
        return self._parse(resp)

    async def accept_invite(self, invite_id: str | UUID) -> ApiResponse:
        resp = await self._post(f"/me/invites/{invite_id}:accept")
        return self._parse(resp)

    async def reject_invite(self, invite_id: str | UUID) -> ApiResponse:
        resp = await self._post(f"/me/invites/{invite_id}:reject")
        return self._parse(resp)
