"""E2E tests for cross-service isolation and authorization."""
import pytest

from tests.e2e.clients.user_client import UserApiClient
from tests.e2e.clients.workspace_client import WorkspaceApiClient
from tests.e2e.clients.category_client import CategoryApiClient
from tests.e2e.clients.expense_client import ExpenseApiClient
from tests.e2e.helpers.test_data import (
    unique_email, strong_password, category_name,
)

pytestmark = pytest.mark.cross_service


class TestWorkspaceIsolation:

    async def test_user_cannot_see_other_workspace_categories(self):
        """User A creates a category in their workspace; User B should not see it."""
        # User A
        user_a = UserApiClient()
        a_data = (await user_a.register_and_auth(unique_email(), strong_password())).raise_on_error()

        ws_a = WorkspaceApiClient()
        ws_a.set_token(a_data["access_token"])
        ws_list_a = (await ws_a.list_all()).raise_on_error()
        workspaces_a = ws_list_a.get("workspaces", ws_list_a) if isinstance(ws_list_a, dict) else ws_list_a
        ws_a_id = str(workspaces_a[0]["id"])

        cat_a = CategoryApiClient()
        cat_a.set_token(a_data["access_token"])
        cat_a.set_workspace_id(ws_a_id)
        created = (await cat_a.create(category_name("UserA"))).raise_on_error()

        # User B
        user_b = UserApiClient()
        b_data = (await user_b.register_and_auth(unique_email(), strong_password())).raise_on_error()

        ws_b = WorkspaceApiClient()
        ws_b.set_token(b_data["access_token"])
        ws_list_b = (await ws_b.list_all()).raise_on_error()
        workspaces_b = ws_list_b.get("workspaces", ws_list_b) if isinstance(ws_list_b, dict) else ws_list_b
        ws_b_id = str(workspaces_b[0]["id"])

        cat_b = CategoryApiClient()
        cat_b.set_token(b_data["access_token"])
        cat_b.set_workspace_id(ws_b_id)

        # User B's categories should not include User A's
        b_categories = (await cat_b.list_all()).raise_on_error()
        items = b_categories if isinstance(b_categories, list) else b_categories.get("items", [])
        b_cat_ids = [c["id"] for c in items]
        assert created["id"] not in b_cat_ids

    async def test_non_member_cannot_access_workspace_expenses(self):
        """A user not in the workspace cannot create expenses there."""
        # Owner
        owner = UserApiClient()
        o_data = (await owner.register_and_auth(unique_email(), strong_password())).raise_on_error()

        ws_client = WorkspaceApiClient()
        ws_client.set_token(o_data["access_token"])
        ws_list = (await ws_client.list_all()).raise_on_error()
        workspaces = ws_list.get("workspaces", ws_list) if isinstance(ws_list, dict) else ws_list
        ws_id = str(workspaces[0]["id"])

        # Outsider
        outsider = UserApiClient()
        out_data = (await outsider.register_and_auth(unique_email(), strong_password())).raise_on_error()
        exp = ExpenseApiClient()
        exp.set_token(out_data["access_token"])
        exp.set_workspace_id(ws_id)

        result = await exp.create(amount=10.0, description="Unauthorized")
        assert not result.ok
        assert result.status_code in (400, 403, 404)


class TestMemberAuthorization:

    async def test_invited_member_can_access_workspace(self):
        """After accepting invite, member can create resources in the workspace."""
        # Owner
        owner_api = UserApiClient()
        owner_data = (await owner_api.register_and_auth(unique_email(), strong_password())).raise_on_error()

        ws = WorkspaceApiClient()
        ws.set_token(owner_data["access_token"])
        ws_list = (await ws.list_all()).raise_on_error()
        workspaces = ws_list.get("workspaces", ws_list) if isinstance(ws_list, dict) else ws_list
        ws_id = str(workspaces[0]["id"])

        # Member
        member_email = unique_email()
        member_api = UserApiClient()
        member_data = (await member_api.register_and_auth(member_email, strong_password())).raise_on_error()

        # Owner invites member
        invite = (await ws.create_invite(ws_id, member_email, role="full")).raise_on_error()

        # Member accepts
        member_ws = WorkspaceApiClient()
        member_ws.set_token(member_data["access_token"])
        await member_ws.accept_invite(invite["id"])

        # Member can now create categories in workspace
        member_cat = CategoryApiClient()
        member_cat.set_token(member_data["access_token"])
        member_cat.set_workspace_id(ws_id)
        result = await member_cat.create(category_name("MemberCat"))
        assert result.ok


class TestUnauthenticated:

    async def test_no_token_gets_rejected(self):
        """Requests without authentication are rejected."""
        cat = CategoryApiClient()
        cat.set_workspace_id("550e8400-e29b-41d4-a716-446655440000")
        result = await cat.list_all()
        assert not result.ok
        assert result.status_code in (401, 403)
