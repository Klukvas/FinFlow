"""
Unit tests for Internal API Router.

Tests cover:
- POST /internal/workspaces/{id}/authorize - Authorize user
- GET /internal/users/{id}/workspaces - Get user workspaces
- GET /internal/users/{id}/default-workspace - Get default workspace
- POST /internal/workspaces/personal - Create personal workspace
- GET /internal/workspaces/{id}/role/{user_id} - Get user role
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timezone
from uuid import uuid4

from app.models.workspace import WorkspaceType
from app.models.member import MemberRole


# ==================== Authorize ====================


class TestAuthorizeEndpoint:
    """Tests for POST /internal/workspaces/{workspace_id}/authorize."""

    @patch("app.services.workspace.WorkspaceService.get_user_role")
    @patch("app.services.workspace.WorkspaceService.authorize")
    def test_authorize_success(
        self, mock_auth, mock_role, client, shared_workspace, internal_headers
    ):
        mock_auth.return_value = True
        mock_role.return_value = MemberRole.OWNER

        response = client.post(
            f"/internal/workspaces/{shared_workspace.id}/authorize",
            json={"user_id": 1, "required_role": "read"},
            headers=internal_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authorized"] is True
        assert data["role"] == "owner"
        assert data["user_id"] == 1

    @patch("app.services.workspace.WorkspaceService.get_user_role")
    @patch("app.services.workspace.WorkspaceService.authorize")
    def test_authorize_denied(
        self, mock_auth, mock_role, client, shared_workspace, internal_headers
    ):
        mock_auth.return_value = False
        mock_role.return_value = None

        response = client.post(
            f"/internal/workspaces/{shared_workspace.id}/authorize",
            json={"user_id": 99, "required_role": "owner"},
            headers=internal_headers,
        )
        assert response.status_code == 403

    @patch("app.services.workspace.WorkspaceService.get_user_role")
    @patch("app.services.workspace.WorkspaceService.authorize")
    def test_authorize_with_legacy_role_name(
        self, mock_auth, mock_role, client, shared_workspace, internal_headers
    ):
        """Old role names (member/admin/viewer) should be migrated."""
        mock_auth.return_value = True
        mock_role.return_value = MemberRole.FULL

        response = client.post(
            f"/internal/workspaces/{shared_workspace.id}/authorize",
            json={"user_id": 1, "required_role": "admin"},
            headers=internal_headers,
        )
        assert response.status_code == 200

    def test_authorize_missing_user_id(
        self, client, shared_workspace, internal_headers
    ):
        response = client.post(
            f"/internal/workspaces/{shared_workspace.id}/authorize",
            json={"required_role": "read"},
            headers=internal_headers,
        )
        assert response.status_code == 400


# ==================== Get User Workspaces ====================


class TestGetUserWorkspacesEndpoint:
    """Tests for GET /internal/users/{user_id}/workspaces."""

    @patch("app.services.workspace.WorkspaceService.get_user_role")
    @patch("app.services.workspace.WorkspaceService.get_user_default_workspace")
    @patch("app.services.workspace.WorkspaceService.get_user_workspaces")
    def test_success(
        self, mock_list, mock_default, mock_role,
        client, shared_workspace, internal_headers
    ):
        mock_list.return_value = [shared_workspace]
        mock_default.return_value = shared_workspace
        mock_role.return_value = MemberRole.OWNER

        # Mock the type attribute
        type(shared_workspace).type = PropertyMock(return_value=WorkspaceType.SHARED)

        response = client.get(
            "/internal/users/1/workspaces", headers=internal_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "workspaces" in data
        assert len(data["workspaces"]) == 1

    @patch("app.services.workspace.WorkspaceService.get_user_default_workspace")
    @patch("app.services.workspace.WorkspaceService.get_user_workspaces")
    def test_empty(self, mock_list, mock_default, client, internal_headers):
        mock_list.return_value = []
        mock_default.return_value = None

        response = client.get(
            "/internal/users/999/workspaces", headers=internal_headers
        )
        assert response.status_code == 200
        assert response.json()["workspaces"] == []

    @patch("app.services.workspace.WorkspaceService.get_user_role")
    @patch("app.services.workspace.WorkspaceService.get_user_default_workspace")
    @patch("app.services.workspace.WorkspaceService.get_user_workspaces")
    def test_is_default_flag(
        self, mock_list, mock_default, mock_role,
        client, shared_workspace, internal_headers
    ):
        """is_default should be True when workspace matches default."""
        mock_list.return_value = [shared_workspace]
        mock_default.return_value = shared_workspace
        mock_role.return_value = MemberRole.OWNER
        type(shared_workspace).type = PropertyMock(return_value=WorkspaceType.PERSONAL)

        response = client.get(
            "/internal/users/1/workspaces", headers=internal_headers
        )
        ws = response.json()["workspaces"][0]
        assert ws["is_default"] is True


# ==================== Get Default Workspace ====================


class TestGetDefaultWorkspaceEndpoint:
    """Tests for GET /internal/users/{user_id}/default-workspace."""

    @patch("app.services.workspace.WorkspaceService.get_user_default_workspace")
    def test_success(self, mock_default, client, shared_workspace, internal_headers):
        type(shared_workspace).type = PropertyMock(return_value=WorkspaceType.PERSONAL)
        mock_default.return_value = shared_workspace

        response = client.get(
            "/internal/users/1/default-workspace", headers=internal_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "workspace_id" in data
        assert data["type"] == "personal"

    @patch("app.services.workspace.WorkspaceService.get_user_default_workspace")
    def test_not_found(self, mock_default, client, internal_headers):
        mock_default.return_value = None

        response = client.get(
            "/internal/users/999/default-workspace", headers=internal_headers
        )
        assert response.status_code == 404


# ==================== Create Personal Workspace ====================


class TestCreatePersonalWorkspaceEndpoint:
    """Tests for POST /internal/workspaces/personal."""

    @patch("app.services.workspace.WorkspaceService.create_personal_workspace")
    def test_success(self, mock_create, client, internal_headers):
        mock_ws = MagicMock()
        mock_ws.id = uuid4()
        mock_create.return_value = mock_ws

        response = client.post(
            "/internal/workspaces/personal",
            json={"user_id": 42},
            headers=internal_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "workspace_id" in data

    @patch("app.services.workspace.WorkspaceService.create_personal_workspace")
    def test_creation_failure(self, mock_create, client, internal_headers):
        from app.exceptions import WorkspaceValidationError

        mock_create.side_effect = WorkspaceValidationError("Failed to create")

        response = client.post(
            "/internal/workspaces/personal",
            json={"user_id": 42},
            headers=internal_headers,
        )
        assert response.status_code == 400

    def test_missing_user_id(self, client, internal_headers):
        response = client.post(
            "/internal/workspaces/personal",
            json={},
            headers=internal_headers,
        )
        assert response.status_code == 400


# ==================== Get User Role ====================


class TestGetUserRoleEndpoint:
    """Tests for GET /internal/workspaces/{workspace_id}/role/{user_id}."""

    @patch("app.services.workspace.WorkspaceService.get_user_role")
    def test_success(self, mock_role, client, shared_workspace, internal_headers):
        mock_role.return_value = MemberRole.FULL

        response = client.get(
            f"/internal/workspaces/{shared_workspace.id}/role/2",
            headers=internal_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "full"
        assert data["user_id"] == 2

    @patch("app.services.workspace.WorkspaceService.get_user_role")
    def test_not_member(self, mock_role, client, shared_workspace, internal_headers):
        mock_role.return_value = None

        response = client.get(
            f"/internal/workspaces/{shared_workspace.id}/role/999",
            headers=internal_headers,
        )
        assert response.status_code == 404

    @patch("app.services.workspace.WorkspaceService.get_user_role")
    def test_owner_role(self, mock_role, client, shared_workspace, internal_headers):
        mock_role.return_value = MemberRole.OWNER

        response = client.get(
            f"/internal/workspaces/{shared_workspace.id}/role/1",
            headers=internal_headers,
        )
        assert response.status_code == 200
        assert response.json()["role"] == "owner"
