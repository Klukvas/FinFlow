"""
Unit tests for Member API Routers.

Tests cover:
- GET /workspaces/{workspace_id}/members - List members
- PATCH /workspaces/{workspace_id}/members/{user_id} - Update member role
- DELETE /workspaces/{workspace_id}/members/{user_id} - Remove member
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from uuid import uuid4

from app.models.member import MemberRole, MemberStatus, WorkspaceMember
from app.schemas.member import MemberResponse


class TestGetMembersEndpoint:
    """Tests for GET /workspaces/{workspace_id}/members"""

    @patch('app.services.workspace.WorkspaceService.get_members')
    def test_get_members_success(
        self, mock_get, client, shared_workspace, auth_headers
    ):
        """Successfully get workspace members"""
        mock_response = MemberResponse(
            id=1,
            workspace_id=shared_workspace.id,
            user_id=1,
            role=MemberRole.OWNER,
            status=MemberStatus.ACTIVE,
            joined_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=None,
            email="owner@test.com",
            username="owner"
        )
        mock_get.return_value = [mock_response]
        
        response = client.get(
            f"/workspaces/{shared_workspace.id}/members",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        assert len(data["members"]) == 1

    @patch('app.services.workspace.WorkspaceService.get_members')
    def test_get_members_includes_user_details(
        self, mock_get, client, shared_workspace, auth_headers
    ):
        """Members response includes user details"""
        mock_response = MemberResponse(
            id=1,
            workspace_id=shared_workspace.id,
            user_id=1,
            role=MemberRole.OWNER,
            status=MemberStatus.ACTIVE,
            joined_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=None,
            email="owner@test.com",
            username="owner"
        )
        mock_get.return_value = [mock_response]
        
        response = client.get(
            f"/workspaces/{shared_workspace.id}/members",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        member = response.json()["members"][0]
        
        assert "email" in member
        assert "username" in member
        assert member["email"] == "owner@test.com"
        assert member["username"] == "owner"

    # Note: Can't test truly unauthorized requests - TestClient always has user_id=1

    @patch('app.services.workspace.WorkspaceService.get_members')
    def test_get_members_nonexistent_workspace(
        self, mock_get, client, auth_headers
    ):
        """Handle non-existent workspace"""
        from app.exceptions import WorkspaceNotFoundError
        
        fake_id = uuid4()
        mock_get.side_effect = WorkspaceNotFoundError(fake_id)
        
        response = client.get(
            f"/workspaces/{fake_id}/members",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestUpdateMemberRoleEndpoint:
    """Tests for PATCH /workspaces/{workspace_id}/members/{user_id}"""

    @patch('app.services.workspace.WorkspaceService.update_member_role')
    def test_update_role_success(
        self, mock_update, client, shared_workspace, auth_headers
    ):
        """Successfully update member role"""
        mock_member = MagicMock()
        mock_member.id = 2
        mock_member.workspace_id = shared_workspace.id
        mock_member.user_id = 2
        mock_member.role = MemberRole.FULL
        mock_member.status = MemberStatus.ACTIVE
        mock_member.joined_at = datetime.utcnow()
        mock_member.created_at = datetime.utcnow()
        mock_member.updated_at = None
        mock_update.return_value = mock_member
        
        response = client.patch(
            f"/workspaces/{shared_workspace.id}/members/2",
            json={"role": "full"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "full"

    @patch('app.services.workspace.WorkspaceService.update_member_role')
    def test_update_role_to_read(
        self, mock_update, client, shared_workspace, auth_headers
    ):
        """Update member role to read"""
        mock_member = MagicMock()
        mock_member.id = 2
        mock_member.workspace_id = shared_workspace.id
        mock_member.user_id = 2
        mock_member.role = MemberRole.READ
        mock_member.status = MemberStatus.ACTIVE
        mock_member.joined_at = datetime.utcnow()
        mock_member.created_at = datetime.utcnow()
        mock_member.updated_at = None
        mock_update.return_value = mock_member
        
        response = client.patch(
            f"/workspaces/{shared_workspace.id}/members/2",
            json={"role": "read"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "read"

    def test_update_role_invalid_role(
        self, client, shared_workspace, auth_headers
    ):
        """Reject invalid role value (returns 400 via custom exception handler)"""
        response = client.patch(
            f"/workspaces/{shared_workspace.id}/members/2",
            json={"role": "invalid"},
            headers=auth_headers
        )
        
        assert response.status_code == 400  # Custom validation handler returns 400

    def test_update_role_cannot_set_owner(
        self, client, shared_workspace, auth_headers
    ):
        """Cannot set role to owner (returns 400 via custom exception handler)"""
        response = client.patch(
            f"/workspaces/{shared_workspace.id}/members/2",
            json={"role": "owner"},
            headers=auth_headers
        )
        
        assert response.status_code == 400  # Custom validation handler returns 400

    # Note: Can't test truly unauthorized requests - TestClient always has user_id=1

    @patch('app.services.workspace.WorkspaceService.update_member_role')
    def test_update_role_non_owner_fails(
        self, mock_update, client, shared_workspace, auth_headers
    ):
        """Non-owner cannot update roles"""
        from app.exceptions import WorkspaceAccessDeniedError
        
        mock_update.side_effect = WorkspaceAccessDeniedError(
            "Only the workspace owner can change member roles"
        )
        
        response = client.patch(
            f"/workspaces/{shared_workspace.id}/members/2",
            json={"role": "full"},
            headers=auth_headers
        )
        
        assert response.status_code == 403

    @patch('app.services.workspace.WorkspaceService.update_member_role')
    def test_update_role_member_not_found(
        self, mock_update, client, shared_workspace, auth_headers
    ):
        """Handle non-existent member"""
        from app.exceptions import MemberNotFoundError
        
        mock_update.side_effect = MemberNotFoundError(999, shared_workspace.id)
        
        response = client.patch(
            f"/workspaces/{shared_workspace.id}/members/999",
            json={"role": "full"},
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestRemoveMemberEndpoint:
    """Tests for DELETE /workspaces/{workspace_id}/members/{user_id}"""

    @patch('app.services.workspace.WorkspaceService.remove_member')
    def test_remove_member_success(
        self, mock_remove, client, shared_workspace, auth_headers
    ):
        """Successfully remove member"""
        mock_remove.return_value = None
        
        response = client.delete(
            f"/workspaces/{shared_workspace.id}/members/2",
            headers=auth_headers
        )
        
        assert response.status_code == 204

    # Note: Can't test truly unauthorized requests - TestClient always has user_id=1

    @patch('app.services.workspace.WorkspaceService.remove_member')
    def test_remove_member_non_owner_fails(
        self, mock_remove, client, shared_workspace, auth_headers
    ):
        """Non-owner cannot remove members"""
        from app.exceptions import WorkspaceAccessDeniedError
        
        mock_remove.side_effect = WorkspaceAccessDeniedError(
            "Only the workspace owner can remove members"
        )
        
        response = client.delete(
            f"/workspaces/{shared_workspace.id}/members/2",
            headers=auth_headers
        )
        
        assert response.status_code == 403

    @patch('app.services.workspace.WorkspaceService.remove_member')
    def test_remove_owner_fails(
        self, mock_remove, client, shared_workspace, auth_headers
    ):
        """Cannot remove workspace owner"""
        from app.exceptions import InvalidRoleChangeError
        
        mock_remove.side_effect = InvalidRoleChangeError(
            "Cannot remove the workspace owner"
        )
        
        response = client.delete(
            f"/workspaces/{shared_workspace.id}/members/1",
            headers=auth_headers
        )
        
        assert response.status_code == 400

    @patch('app.services.workspace.WorkspaceService.remove_member')
    def test_remove_member_not_found(
        self, mock_remove, client, shared_workspace, auth_headers
    ):
        """Handle non-existent member"""
        from app.exceptions import MemberNotFoundError
        
        mock_remove.side_effect = MemberNotFoundError(999, shared_workspace.id)
        
        response = client.delete(
            f"/workspaces/{shared_workspace.id}/members/999",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    @patch('app.services.workspace.WorkspaceService.remove_member')
    def test_remove_member_archived_workspace(
        self, mock_remove, client, shared_workspace, auth_headers
    ):
        """Cannot remove from archived workspace"""
        from app.exceptions import WorkspaceArchivedError
        
        mock_remove.side_effect = WorkspaceArchivedError(shared_workspace.id)
        
        response = client.delete(
            f"/workspaces/{shared_workspace.id}/members/2",
            headers=auth_headers
        )
        
        assert response.status_code == 400


class TestMemberResponseFormat:
    """Tests for member response serialization"""

    @patch('app.services.workspace.WorkspaceService.get_members')
    def test_member_response_has_all_fields(
        self, mock_get, client, shared_workspace, auth_headers
    ):
        """Verify member response contains all expected fields"""
        now = datetime.utcnow()
        mock_response = MemberResponse(
            id=1,
            workspace_id=shared_workspace.id,
            user_id=1,
            role=MemberRole.OWNER,
            status=MemberStatus.ACTIVE,
            joined_at=now,
            created_at=now,
            updated_at=now,
            email="owner@test.com",
            username="owner"
        )
        mock_get.return_value = [mock_response]
        
        response = client.get(
            f"/workspaces/{shared_workspace.id}/members",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        member = response.json()["members"][0]
        
        # Check required fields
        assert "id" in member
        assert "workspace_id" in member
        assert "user_id" in member
        assert "role" in member
        assert "status" in member
        assert "joined_at" in member
        assert "created_at" in member
        assert "email" in member
        assert "username" in member

    @patch('app.services.workspace.WorkspaceService.get_members')
    def test_member_role_values(
        self, mock_get, client, shared_workspace, auth_headers
    ):
        """Verify role values are correctly serialized"""
        now = datetime.utcnow()
        
        members = [
            MemberResponse(
                id=1, workspace_id=shared_workspace.id, user_id=1,
                role=MemberRole.OWNER, status=MemberStatus.ACTIVE,
                joined_at=now, created_at=now, updated_at=None,
                email="owner@test.com", username="owner"
            ),
            MemberResponse(
                id=2, workspace_id=shared_workspace.id, user_id=2,
                role=MemberRole.FULL, status=MemberStatus.ACTIVE,
                joined_at=now, created_at=now, updated_at=None,
                email="full@test.com", username="full_user"
            ),
            MemberResponse(
                id=3, workspace_id=shared_workspace.id, user_id=3,
                role=MemberRole.READ, status=MemberStatus.ACTIVE,
                joined_at=now, created_at=now, updated_at=None,
                email="read@test.com", username="read_user"
            ),
        ]
        mock_get.return_value = members
        
        response = client.get(
            f"/workspaces/{shared_workspace.id}/members",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()["members"]
        
        roles = [m["role"] for m in data]
        assert "owner" in roles
        assert "full" in roles
        assert "read" in roles
