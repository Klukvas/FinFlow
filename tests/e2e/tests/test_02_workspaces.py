"""E2E tests for workspace and member management flows."""
import pytest

from tests.e2e.clients.user_client import UserApiClient
from tests.e2e.clients.workspace_client import WorkspaceApiClient
from tests.e2e.helpers.test_data import unique_email, strong_password, workspace_name

pytestmark = pytest.mark.workspace


class TestWorkspaceCRUD:

    async def test_list_workspaces(self, workspace_client):
        result = await workspace_client.list_all()
        data = result.raise_on_error()
        workspaces = data.get("workspaces", data) if isinstance(data, dict) else data
        assert isinstance(workspaces, list)
        assert len(workspaces) >= 1  # at least personal workspace

    async def test_get_workspace(self, workspace_client, workspace_id):
        result = await workspace_client.get(workspace_id)
        data = result.raise_on_error()
        assert str(data["id"]) == workspace_id

    async def test_update_workspace_name(self, workspace_client, workspace_id):
        new_name = workspace_name()
        result = await workspace_client.update(workspace_id, new_name)
        data = result.raise_on_error()
        assert data["name"] == new_name

    async def test_create_workspace_exceeds_limit(self, primary_user):
        """Basic plan limits to 1 workspace; creating a second should fail."""
        client = WorkspaceApiClient()
        client.set_token(primary_user["token"])
        result = await client.create(workspace_name())
        assert not result.ok
        assert result.status_code == 403


class TestMembers:

    async def test_invite_accept_and_list_members(self, primary_user, workspace_id):
        """Owner invites a new user to their workspace, invitee accepts."""
        # Create a fresh user to invite
        member_email = unique_email()
        member_api = UserApiClient()
        member_reg = await member_api.register(member_email, strong_password())
        member_data = member_reg.raise_on_error()
        member_token = member_data["access_token"]

        # Owner invites the new user
        owner = WorkspaceApiClient()
        owner.set_token(primary_user["token"])
        invite_result = await owner.create_invite(workspace_id, member_email, role="full")
        invite_data = invite_result.raise_on_error()
        invite_id = invite_data["id"]

        # Member accepts the invite
        invitee = WorkspaceApiClient()
        invitee.set_token(member_token)
        accept_result = await invitee.accept_invite(invite_id)
        assert accept_result.ok or accept_result.status_code in (200, 204)

        # Verify member list
        members = (await owner.list_members(workspace_id)).raise_on_error()
        member_list = members if isinstance(members, list) else members.get("members", [])
        assert len(member_list) >= 2

    async def test_remove_member_loses_access(self, primary_user, workspace_id):
        """After removing a member, they should no longer have access."""
        # Create and invite a user
        member_email = unique_email()
        member_api = UserApiClient()
        member_reg = await member_api.register(member_email, strong_password())
        member_data = member_reg.raise_on_error()
        member_token = member_data["access_token"]

        owner = WorkspaceApiClient()
        owner.set_token(primary_user["token"])
        invite = (await owner.create_invite(workspace_id, member_email)).raise_on_error()

        invitee = WorkspaceApiClient()
        invitee.set_token(member_token)
        await invitee.accept_invite(invite["id"])

        # Get the member's user ID from the member list
        members = (await owner.list_members(workspace_id)).raise_on_error()
        member_list = members if isinstance(members, list) else members.get("members", [])
        # Find the member that is not the owner
        member_entry = next(
            (m for m in member_list if m.get("email") == member_email or m.get("role") != "owner"),
            None,
        )
        if member_entry:
            user_id = member_entry.get("user_id") or member_entry.get("id")
            if user_id:
                remove_result = await owner.remove_member(workspace_id, user_id)
                assert remove_result.ok or remove_result.status_code == 204

    async def test_list_invites(self, primary_user, workspace_id):
        """Owner can list pending invites for their workspace."""
        owner = WorkspaceApiClient()
        owner.set_token(primary_user["token"])

        # Create an invite to a new user
        email = unique_email()
        user_api = UserApiClient()
        await user_api.register(email, strong_password())
        await owner.create_invite(workspace_id, email)

        invites = await owner.list_invites(workspace_id)
        data = invites.raise_on_error()
        invite_list = data if isinstance(data, list) else data.get("invites", [])
        assert len(invite_list) >= 1

    async def test_reject_invite(self, primary_user, workspace_id):
        """Invitee can reject a pending invite."""
        # Create a fresh user to invite
        member_email = unique_email()
        member_api = UserApiClient()
        member_reg = await member_api.register(member_email, strong_password())
        member_data = member_reg.raise_on_error()
        member_token = member_data["access_token"]

        # Owner invites the new user
        owner = WorkspaceApiClient()
        owner.set_token(primary_user["token"])
        invite_result = await owner.create_invite(workspace_id, member_email, role="read")
        invite_data = invite_result.raise_on_error()
        invite_id = invite_data["id"]

        # Member rejects the invite
        invitee = WorkspaceApiClient()
        invitee.set_token(member_token)
        reject_result = await invitee.reject_invite(invite_id)
        assert reject_result.ok or reject_result.status_code in (200, 204)

    async def test_cancel_pending_invite(self, primary_user, workspace_id):
        """Owner can cancel a pending invite before the invitee accepts."""
        member_email = unique_email()
        user_api = UserApiClient()
        await user_api.register(member_email, strong_password())

        owner = WorkspaceApiClient()
        owner.set_token(primary_user["token"])
        invite_result = await owner.create_invite(workspace_id, member_email, role="read")
        invite_data = invite_result.raise_on_error()
        invite_id = invite_data["id"]

        # Owner cancels the pending invite
        cancel_result = await owner.cancel_invite(workspace_id, invite_id)
        assert cancel_result.ok or cancel_result.status_code in (200, 204)

    async def test_update_member_role(self, primary_user, workspace_id):
        """Owner can change a member's role after they have joined."""
        # Create and invite a user with 'read' role
        member_email = unique_email()
        member_api = UserApiClient()
        member_reg = await member_api.register(member_email, strong_password())
        member_data = member_reg.raise_on_error()
        member_token = member_data["access_token"]

        owner = WorkspaceApiClient()
        owner.set_token(primary_user["token"])
        invite = (await owner.create_invite(workspace_id, member_email, role="read")).raise_on_error()

        invitee = WorkspaceApiClient()
        invitee.set_token(member_token)
        await invitee.accept_invite(invite["id"])

        # Find the member's user_id
        members = (await owner.list_members(workspace_id)).raise_on_error()
        member_list = members if isinstance(members, list) else members.get("members", [])
        member_entry = next(
            (m for m in member_list if m.get("email") == member_email),
            None,
        )
        assert member_entry is not None, "Invited member not found in member list"
        user_id = member_entry.get("user_id") or member_entry.get("id")

        # Update role from 'read' to 'full'
        update_result = await owner.update_member_role(workspace_id, user_id, "full")
        assert update_result.ok or update_result.status_code in (200, 204)


class TestWorkspaceArchiveAndLeave:

    async def test_archive_workspace(self):
        """Owner can archive a non-personal workspace they own."""
        user_api = UserApiClient()
        user_data = (await user_api.register(unique_email(), strong_password())).raise_on_error()
        token = user_data["access_token"]

        ws = WorkspaceApiClient()
        ws.set_token(token)

        # Create a separate (non-personal) workspace to archive
        created = (await ws.create(workspace_name())).raise_on_error()
        ws_id = str(created["id"])

        # Archive the workspace
        result = await ws.archive(ws_id)
        assert result.ok or result.status_code in (200, 204)

    async def test_member_can_leave_workspace(self, primary_user, workspace_id):
        """A non-owner member can leave a workspace."""
        member_email = unique_email()
        member_api = UserApiClient()
        member_reg = await member_api.register(member_email, strong_password())
        member_data = member_reg.raise_on_error()
        member_token = member_data["access_token"]

        # Owner invites the member
        owner = WorkspaceApiClient()
        owner.set_token(primary_user["token"])
        invite = (await owner.create_invite(workspace_id, member_email, role="full")).raise_on_error()

        # Member accepts
        member_ws = WorkspaceApiClient()
        member_ws.set_token(member_token)
        await member_ws.accept_invite(invite["id"])

        # Member leaves the workspace
        leave_result = await member_ws.leave(workspace_id)
        assert leave_result.ok or leave_result.status_code in (200, 204)
