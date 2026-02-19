"""
Unit tests for Invite API Routers.

Tests cover:
- POST /workspaces/{workspace_id}/invites - Create invite
- GET /workspaces/{workspace_id}/invites - List workspace invites
- DELETE /workspaces/{workspace_id}/invites/{invite_id} - Cancel invite
- GET /me/invites - List my invites
- POST /me/invites/{invite_id}:accept - Accept invite
- POST /me/invites/{invite_id}:reject - Reject invite
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.invite import InviteStatus
from app.models.member import MemberRole, MemberStatus, WorkspaceMember
from app.clients.user import UserInfo


class TestCreateInviteEndpoint:
    """Tests for POST /workspaces/{workspace_id}/invites"""

    @patch('app.services.invite.InviteService.create_invite')
    def test_create_invite_success(
        self, mock_create, client, shared_workspace, auth_headers, pending_invite
    ):
        """Successfully create invite via API"""
        pending_invite.workspace = shared_workspace
        mock_create.return_value = (pending_invite, True)
        
        response = client.post(
            f"/workspaces/{shared_workspace.id}/invites",
            json={"email": "member@test.com", "role": "full"},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert "id" in data

    @patch('app.services.invite.InviteService.create_invite')
    def test_create_invite_returns_existing(
        self, mock_create, client, shared_workspace, auth_headers, pending_invite
    ):
        """Return existing invite when duplicate (idempotent)"""
        pending_invite.workspace = shared_workspace
        mock_create.return_value = (pending_invite, False)  # is_new=False
        
        response = client.post(
            f"/workspaces/{shared_workspace.id}/invites",
            json={"email": "member@test.com", "role": "read"},
            headers=auth_headers
        )
        
        assert response.status_code == 201

    def test_create_invite_invalid_email(
        self, client, shared_workspace, auth_headers
    ):
        """Reject invalid email format (returns 400 via custom exception handler)"""
        response = client.post(
            f"/workspaces/{shared_workspace.id}/invites",
            json={"email": "not-an-email", "role": "read"},
            headers=auth_headers
        )
        
        assert response.status_code == 400  # Custom validation handler returns 400

    def test_create_invite_invalid_role(
        self, client, shared_workspace, auth_headers
    ):
        """Reject invalid role (returns 400 via custom exception handler)"""
        response = client.post(
            f"/workspaces/{shared_workspace.id}/invites",
            json={"email": "member@test.com", "role": "invalid"},
            headers=auth_headers
        )
        
        assert response.status_code == 400  # Custom validation handler returns 400

    def test_create_invite_missing_email(
        self, client, shared_workspace, auth_headers
    ):
        """Reject request with missing email field"""
        response = client.post(
            f"/workspaces/{shared_workspace.id}/invites",
            json={"role": "read"},  # missing email
            headers=auth_headers
        )
        
        assert response.status_code == 400  # Custom validation handler returns 400

    # Note: Can't test truly unauthorized requests - TestClient always has user_id=1


class TestListWorkspaceInvitesEndpoint:
    """Tests for GET /workspaces/{workspace_id}/invites"""

    @patch('app.services.invite.InviteService.get_workspace_invites')
    def test_list_invites_success(
        self, mock_list, client, shared_workspace, auth_headers, pending_invite
    ):
        """Successfully list workspace invites"""
        pending_invite.workspace = shared_workspace
        mock_list.return_value = [pending_invite]
        
        response = client.get(
            f"/workspaces/{shared_workspace.id}/invites",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "invites" in data
        assert len(data["invites"]) == 1

    def test_list_invites_with_status_filter(
        self, client, shared_workspace, auth_headers
    ):
        """List invites with status filter returns 200"""
        response = client.get(
            f"/workspaces/{shared_workspace.id}/invites?status=accepted",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "invites" in data

    # Note: Can't test truly unauthorized requests - TestClient always has user_id=1


class TestCancelInviteEndpoint:
    """Tests for DELETE /workspaces/{workspace_id}/invites/{invite_id}"""

    @patch('app.services.invite.InviteService.cancel_invite')
    def test_cancel_invite_success(
        self, mock_cancel, client, shared_workspace, pending_invite, auth_headers
    ):
        """Successfully cancel invite"""
        mock_cancel.return_value = None
        
        response = client.delete(
            f"/workspaces/{shared_workspace.id}/invites/{pending_invite.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204

    # Note: Can't test truly unauthorized requests - TestClient always has user_id=1


class TestGetMyInvitesEndpoint:
    """Tests for GET /me/invites"""

    @patch('app.services.invite.InviteService.get_my_invites')
    def test_get_my_invites_success(self, mock_get, client, auth_headers):
        """Successfully get my invites"""
        from app.schemas.invite import MyInviteResponse

        mock_response = MyInviteResponse(
            id=uuid4(),
            workspace_id=uuid4(),
            workspace_name="Test Workspace",
            inviter_user_id=1,
            inviter_email="owner@test.com",
            role=MemberRole.FULL,
            status=InviteStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=3),
            created_at=datetime.utcnow(),
        )
        mock_get.return_value = [mock_response]

        response = client.get("/me/invites", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "invites" in data
        assert len(data["invites"]) == 1
        assert data["invites"][0]["workspace_name"] == "Test Workspace"

    @patch('app.services.invite.InviteService.get_my_invites')
    def test_get_my_invites_include_all(self, mock_get, client, auth_headers):
        """Include all invites when requested"""
        mock_get.return_value = []
        
        response = client.get("/me/invites?include_all=true", headers=auth_headers)
        
        assert response.status_code == 200
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args.kwargs.get('include_all') is True

    # Note: Can't test truly unauthorized requests - TestClient always has user_id=1


class TestAcceptInviteEndpoint:
    """Tests for POST /me/invites/{invite_id}:accept"""

    @patch('app.services.invite.InviteService.accept_invite')
    def test_accept_invite_success(
        self, mock_accept, client, pending_invite, auth_headers, shared_workspace
    ):
        """Successfully accept invite"""
        pending_invite.workspace = shared_workspace
        pending_invite.status = InviteStatus.ACCEPTED
        mock_accept.return_value = pending_invite
        
        response = client.post(
            f"/me/invites/{pending_invite.id}:accept",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"

    # Note: Can't test truly unauthorized requests - TestClient always has user_id=1


class TestRejectInviteEndpoint:
    """Tests for POST /me/invites/{invite_id}:reject"""

    @patch('app.services.invite.InviteService.reject_invite')
    def test_reject_invite_success(
        self, mock_reject, client, pending_invite, auth_headers
    ):
        """Successfully reject invite"""
        mock_reject.return_value = None
        
        response = client.post(
            f"/me/invites/{pending_invite.id}:reject",
            headers=auth_headers
        )
        
        assert response.status_code == 204

    # Note: Can't test truly unauthorized requests - TestClient always has user_id=1


class TestInviteResponseFormat:
    """Tests for invite response serialization"""

    @patch('app.services.invite.InviteService.create_invite')
    def test_invite_response_has_all_fields(
        self, mock_create, client, shared_workspace, auth_headers, pending_invite
    ):
        """Verify InviteResponse (owner view) contains all expected fields"""
        pending_invite.workspace = shared_workspace
        mock_create.return_value = (pending_invite, True)
        
        response = client.post(
            f"/workspaces/{shared_workspace.id}/invites",
            json={"email": "member@test.com", "role": "full"},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Check required fields for InviteResponse (owner view)
        # Note: workspace_name and is_actionable are only in MyInviteResponse (invitee view)
        assert "id" in data
        assert "workspace_id" in data
        assert "inviter_user_id" in data
        assert "invitee_user_id" in data
        assert "invitee_email" in data
        assert "role" in data
        assert "status" in data
        assert "expires_at" in data
        assert "created_at" in data
        assert "is_expired" in data

    @patch('app.services.invite.InviteService.get_my_invites')
    def test_my_invite_response_has_inviter_details(
        self, mock_get, client, auth_headers
    ):
        """My invite response includes inviter details"""
        from app.schemas.invite import MyInviteResponse

        mock_response = MyInviteResponse(
            id=uuid4(),
            workspace_id=uuid4(),
            workspace_name="Test Workspace",
            inviter_user_id=1,
            inviter_email="owner@test.com",
            role=MemberRole.FULL,
            status=InviteStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=3),
            created_at=datetime.utcnow(),
        )
        mock_get.return_value = [mock_response]

        response = client.get("/me/invites", headers=auth_headers)

        assert response.status_code == 200
        invite = response.json()["invites"][0]

        assert "inviter_email" in invite
        assert invite["inviter_email"] == "owner@test.com"
