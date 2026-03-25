"""
Unit tests for Workspace CRUD API Routers.

Tests cover:
- POST /workspaces - Create workspace
- GET /workspaces - List workspaces
- GET /workspaces/{id} - Get workspace
- PATCH /workspaces/{id} - Update workspace
- POST /workspaces/{id}:archive - Archive workspace
- POST /workspaces/{id}:unarchive - Unarchive workspace
- POST /workspaces/{id}:leave - Leave workspace
- POST /workspaces/{id}/owner:transfer - Transfer ownership
- GET /workspaces/me/workspaces - Get my workspaces
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timezone
from uuid import uuid4

from app.models.workspace import WorkspaceType
from app.models.member import MemberRole
from app.schemas.workspace import WorkspaceResponse


def _workspace_response(ws_id=None, **overrides) -> WorkspaceResponse:
    """Build a WorkspaceResponse for mocking."""
    defaults = dict(
        id=ws_id or uuid4(),
        name="Test WS",
        type=WorkspaceType.SHARED,
        owner_user_id=1,
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        archived_at=None,
        is_archived=False,
        member_count=1,
        current_user_role="owner",
        is_read_only=False,
    )
    defaults.update(overrides)
    return WorkspaceResponse(**defaults)


# ==================== Create Workspace ====================


class TestCreateWorkspaceEndpoint:
    """Tests for POST /workspaces."""

    @patch("app.services.workspace.WorkspaceService.get_workspace_response")
    @patch("app.services.workspace.WorkspaceService.create_workspace")
    def test_create_success(
        self, mock_create, mock_resp, client, auth_headers
    ):
        mock_ws = MagicMock()
        mock_create.return_value = mock_ws
        resp = _workspace_response()
        mock_resp.return_value = resp

        response = client.post(
            "/workspaces",
            json={"name": "Family Budget", "type": "shared"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test WS"
        mock_create.assert_called_once()

    def test_create_missing_name(self, client, auth_headers):
        response = client.post(
            "/workspaces",
            json={"type": "shared"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_create_empty_name(self, client, auth_headers):
        response = client.post(
            "/workspaces",
            json={"name": "", "type": "shared"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("app.services.workspace.WorkspaceService.create_workspace")
    def test_create_limit_exceeded(self, mock_create, client, auth_headers):
        from app.exceptions import WorkspaceLimitExceededError

        mock_create.side_effect = WorkspaceLimitExceededError(5, 3)
        response = client.post(
            "/workspaces",
            json={"name": "Too many", "type": "shared"},
            headers=auth_headers,
        )
        assert response.status_code == 403


# ==================== List Workspaces ====================


class TestListWorkspacesEndpoint:
    """Tests for GET /workspaces."""

    @patch("app.services.workspace.WorkspaceService.get_workspace_response")
    @patch("app.services.workspace.WorkspaceService.get_user_workspaces")
    def test_list_success(
        self, mock_list, mock_resp, client, shared_workspace, auth_headers
    ):
        mock_list.return_value = [shared_workspace]
        resp = _workspace_response(ws_id=shared_workspace.id)
        mock_resp.return_value = resp

        response = client.get("/workspaces", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "workspaces" in data
        assert "total" in data
        assert data["total"] >= 1

    @patch("app.services.workspace.WorkspaceService.get_user_workspaces")
    def test_list_empty(self, mock_list, client, auth_headers):
        mock_list.return_value = []

        response = client.get("/workspaces", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["workspaces"] == []


# ==================== Get Workspace ====================


class TestGetWorkspaceEndpoint:
    """Tests for GET /workspaces/{workspace_id}."""

    @patch("app.services.workspace.WorkspaceService.get_workspace_response")
    @patch("app.services.workspace.WorkspaceService.get_workspace")
    def test_get_success(
        self, mock_get, mock_resp, client, shared_workspace, auth_headers
    ):
        mock_get.return_value = shared_workspace
        resp = _workspace_response(ws_id=shared_workspace.id)
        mock_resp.return_value = resp

        response = client.get(
            f"/workspaces/{shared_workspace.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    @patch("app.services.workspace.WorkspaceService.get_workspace")
    def test_get_not_found(self, mock_get, client, auth_headers):
        from app.exceptions import WorkspaceNotFoundError

        fake_id = uuid4()
        mock_get.side_effect = WorkspaceNotFoundError(fake_id)

        response = client.get(f"/workspaces/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    @patch("app.services.workspace.WorkspaceService.get_workspace")
    def test_get_access_denied(self, mock_get, client, auth_headers):
        from app.exceptions import WorkspaceAccessDeniedError

        mock_get.side_effect = WorkspaceAccessDeniedError()

        response = client.get(f"/workspaces/{uuid4()}", headers=auth_headers)
        assert response.status_code == 403


# ==================== Update Workspace ====================


class TestUpdateWorkspaceEndpoint:
    """Tests for PATCH /workspaces/{workspace_id}."""

    @patch("app.services.workspace.WorkspaceService.get_workspace_response")
    @patch("app.services.workspace.WorkspaceService.update_workspace")
    def test_update_name_success(
        self, mock_update, mock_resp, client, shared_workspace, auth_headers
    ):
        mock_update.return_value = shared_workspace
        resp = _workspace_response(ws_id=shared_workspace.id, name="New Name")
        mock_resp.return_value = resp

        response = client.patch(
            f"/workspaces/{shared_workspace.id}",
            json={"name": "New Name"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    @patch("app.services.workspace.WorkspaceService.update_workspace")
    def test_update_archived_fails(self, mock_update, client, auth_headers):
        from app.exceptions import WorkspaceArchivedError

        ws_id = uuid4()
        mock_update.side_effect = WorkspaceArchivedError(ws_id)

        response = client.patch(
            f"/workspaces/{ws_id}",
            json={"name": "X"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_update_name_too_long(self, client, shared_workspace, auth_headers):
        response = client.patch(
            f"/workspaces/{shared_workspace.id}",
            json={"name": "x" * 256},
            headers=auth_headers,
        )
        assert response.status_code == 400


# ==================== Archive / Unarchive ====================


class TestArchiveWorkspaceEndpoint:
    """Tests for POST /workspaces/{workspace_id}:archive."""

    @patch("app.services.workspace.WorkspaceService.get_workspace_response")
    @patch("app.services.workspace.WorkspaceService.archive_workspace")
    def test_archive_success(
        self, mock_archive, mock_resp, client, shared_workspace, auth_headers
    ):
        mock_archive.return_value = shared_workspace
        resp = _workspace_response(ws_id=shared_workspace.id, is_archived=True)
        mock_resp.return_value = resp

        response = client.post(
            f"/workspaces/{shared_workspace.id}:archive", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["is_archived"] is True

    @patch("app.services.workspace.WorkspaceService.archive_workspace")
    def test_archive_personal_fails(self, mock_archive, client, auth_headers):
        from app.exceptions import PersonalWorkspaceProtectedError

        mock_archive.side_effect = PersonalWorkspaceProtectedError()
        response = client.post(
            f"/workspaces/{uuid4()}:archive", headers=auth_headers
        )
        assert response.status_code == 400

    @patch("app.services.workspace.WorkspaceService.archive_workspace")
    def test_archive_already_archived_fails(self, mock_archive, client, auth_headers):
        from app.exceptions import WorkspaceArchivedError

        mock_archive.side_effect = WorkspaceArchivedError()
        response = client.post(
            f"/workspaces/{uuid4()}:archive", headers=auth_headers
        )
        assert response.status_code == 400


class TestUnarchiveWorkspaceEndpoint:
    """Tests for POST /workspaces/{workspace_id}:unarchive."""

    @patch("app.services.workspace.WorkspaceService.get_workspace_response")
    @patch("app.services.workspace.WorkspaceService.unarchive_workspace")
    def test_unarchive_success(
        self, mock_unarchive, mock_resp, client, auth_headers
    ):
        ws_id = uuid4()
        mock_ws = MagicMock()
        mock_unarchive.return_value = mock_ws
        resp = _workspace_response(ws_id=ws_id, is_archived=False)
        mock_resp.return_value = resp

        response = client.post(
            f"/workspaces/{ws_id}:unarchive", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["is_archived"] is False

    @patch("app.services.workspace.WorkspaceService.unarchive_workspace")
    def test_unarchive_not_archived_fails(self, mock_unarchive, client, auth_headers):
        from app.exceptions import WorkspaceValidationError

        mock_unarchive.side_effect = WorkspaceValidationError("Workspace is not archived")
        response = client.post(
            f"/workspaces/{uuid4()}:unarchive", headers=auth_headers
        )
        assert response.status_code == 400


# ==================== Leave Workspace ====================


class TestLeaveWorkspaceEndpoint:
    """Tests for POST /workspaces/{workspace_id}:leave."""

    @patch("app.services.workspace.WorkspaceService.leave_workspace")
    def test_leave_success(self, mock_leave, client, auth_headers):
        mock_leave.return_value = None

        response = client.post(
            f"/workspaces/{uuid4()}:leave", headers=auth_headers
        )
        assert response.status_code == 204

    @patch("app.services.workspace.WorkspaceService.leave_workspace")
    def test_leave_owner_fails(self, mock_leave, client, auth_headers):
        from app.exceptions import OwnerCannotLeaveError

        mock_leave.side_effect = OwnerCannotLeaveError()
        response = client.post(
            f"/workspaces/{uuid4()}:leave", headers=auth_headers
        )
        assert response.status_code == 400

    @patch("app.services.workspace.WorkspaceService.leave_workspace")
    def test_leave_personal_fails(self, mock_leave, client, auth_headers):
        from app.exceptions import PersonalWorkspaceProtectedError

        mock_leave.side_effect = PersonalWorkspaceProtectedError("Cannot leave personal workspace")
        response = client.post(
            f"/workspaces/{uuid4()}:leave", headers=auth_headers
        )
        assert response.status_code == 400


# ==================== Transfer Ownership ====================


class TestTransferOwnershipEndpoint:
    """Tests for POST /workspaces/{workspace_id}/owner:transfer."""

    @patch("app.services.workspace.WorkspaceService.get_workspace_response")
    @patch("app.services.workspace.WorkspaceService.transfer_ownership")
    def test_transfer_success(
        self, mock_transfer, mock_resp, client, auth_headers
    ):
        ws_id = uuid4()
        mock_ws = MagicMock()
        mock_transfer.return_value = mock_ws
        resp = _workspace_response(ws_id=ws_id, owner_user_id=2)
        mock_resp.return_value = resp

        response = client.post(
            f"/workspaces/{ws_id}/owner:transfer?new_owner_id=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["owner_user_id"] == 2

    @patch("app.services.workspace.WorkspaceService.transfer_ownership")
    def test_transfer_non_member_fails(self, mock_transfer, client, auth_headers):
        from app.exceptions import MemberNotFoundError

        mock_transfer.side_effect = MemberNotFoundError(user_id=99)
        response = client.post(
            f"/workspaces/{uuid4()}/owner:transfer?new_owner_id=99",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @patch("app.services.workspace.WorkspaceService.transfer_ownership")
    def test_transfer_access_denied(self, mock_transfer, client, auth_headers):
        from app.exceptions import WorkspaceAccessDeniedError

        mock_transfer.side_effect = WorkspaceAccessDeniedError("Only the owner")
        response = client.post(
            f"/workspaces/{uuid4()}/owner:transfer?new_owner_id=2",
            headers=auth_headers,
        )
        assert response.status_code == 403


# ==================== Get My Workspaces ====================


class TestGetMyWorkspacesEndpoint:
    """Tests for GET /workspaces/me/workspaces."""

    @patch("app.services.workspace.WorkspaceService.get_workspace_response")
    @patch("app.services.workspace.WorkspaceService.get_user_workspaces")
    def test_my_workspaces_success(
        self, mock_list, mock_resp, client, shared_workspace, auth_headers
    ):
        mock_list.return_value = [shared_workspace]
        resp = _workspace_response(ws_id=shared_workspace.id)
        mock_resp.return_value = resp

        response = client.get("/workspaces/me/workspaces", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "workspaces" in data
        assert data["total"] >= 1

    @patch("app.services.workspace.WorkspaceService.get_user_workspaces")
    def test_my_workspaces_empty(self, mock_list, client, auth_headers):
        mock_list.return_value = []

        response = client.get("/workspaces/me/workspaces", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0


# ==================== Response Format ====================


class TestWorkspaceResponseFormat:
    """Tests for workspace response serialisation."""

    @patch("app.services.workspace.WorkspaceService.get_workspace_response")
    @patch("app.services.workspace.WorkspaceService.get_workspace")
    def test_response_has_all_fields(
        self, mock_get, mock_resp, client, shared_workspace, auth_headers
    ):
        mock_get.return_value = shared_workspace
        resp = _workspace_response(ws_id=shared_workspace.id)
        mock_resp.return_value = resp

        response = client.get(
            f"/workspaces/{shared_workspace.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        expected_fields = [
            "id", "name", "type", "owner_user_id", "created_at",
            "is_archived", "member_count", "current_user_role", "is_read_only",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
