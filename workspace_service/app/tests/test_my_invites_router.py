"""
Unit tests for My Invites API Router (invitee-facing endpoints).

Tests cover:
- GET /me/invites - List incoming invites
- POST /me/invites/{id}:accept - Accept invite
- POST /me/invites/{id}:reject - Reject invite
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.invite import InviteStatus
from app.models.member import MemberRole
from app.schemas.invite import MyInviteResponse


def _my_invite_response(**overrides) -> MyInviteResponse:
    """Build a MyInviteResponse for mocking."""
    defaults = dict(
        id=uuid4(),
        workspace_id=uuid4(),
        workspace_name="Test Workspace",
        inviter_user_id=1,
        inviter_email="owner@test.com",
        role=MemberRole.FULL,
        status=InviteStatus.PENDING,
        expires_at=datetime.now(timezone.utc) + timedelta(days=3),
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return MyInviteResponse(**defaults)


# ==================== List My Invites ====================


class TestListMyInvitesEndpoint:
    """Tests for GET /me/invites."""

    @patch("app.services.invite.InviteService.get_my_invites")
    def test_list_pending(self, mock_get, client, auth_headers):
        inv = _my_invite_response()
        mock_get.return_value = [inv]

        response = client.get("/me/invites", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["invites"][0]["workspace_name"] == "Test Workspace"

    @patch("app.services.invite.InviteService.get_my_invites")
    def test_list_empty(self, mock_get, client, auth_headers):
        mock_get.return_value = []

        response = client.get("/me/invites", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["invites"] == []

    @patch("app.services.invite.InviteService.get_my_invites")
    def test_include_all_query_param(self, mock_get, client, auth_headers):
        mock_get.return_value = []

        response = client.get("/me/invites?include_all=true", headers=auth_headers)
        assert response.status_code == 200
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs.get("include_all") is True

    @patch("app.services.invite.InviteService.get_my_invites")
    def test_default_include_all_false(self, mock_get, client, auth_headers):
        mock_get.return_value = []

        response = client.get("/me/invites", headers=auth_headers)
        assert response.status_code == 200
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs.get("include_all") is False

    @patch("app.services.invite.InviteService.get_my_invites")
    def test_response_contains_inviter_details(self, mock_get, client, auth_headers):
        inv = _my_invite_response(inviter_email="boss@company.com")
        mock_get.return_value = [inv]

        response = client.get("/me/invites", headers=auth_headers)
        invite_data = response.json()["invites"][0]
        assert invite_data["inviter_email"] == "boss@company.com"

    @patch("app.services.invite.InviteService.get_my_invites")
    def test_response_contains_is_actionable(self, mock_get, client, auth_headers):
        inv = _my_invite_response()
        mock_get.return_value = [inv]

        response = client.get("/me/invites", headers=auth_headers)
        invite_data = response.json()["invites"][0]
        assert "is_actionable" in invite_data

    @patch("app.services.invite.InviteService.get_my_invites")
    def test_response_contains_is_expired(self, mock_get, client, auth_headers):
        inv = _my_invite_response()
        mock_get.return_value = [inv]

        response = client.get("/me/invites", headers=auth_headers)
        invite_data = response.json()["invites"][0]
        assert "is_expired" in invite_data


# ==================== Accept Invite ====================


class TestAcceptInviteEndpoint:
    """Tests for POST /me/invites/{invite_id}:accept."""

    @patch("app.services.invite.InviteService.accept_invite")
    def test_accept_success(
        self, mock_accept, client, pending_invite, shared_workspace, auth_headers
    ):
        pending_invite.workspace = shared_workspace
        pending_invite.status = InviteStatus.ACCEPTED
        mock_accept.return_value = pending_invite

        response = client.post(
            f"/me/invites/{pending_invite.id}:accept", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    @patch("app.services.invite.InviteService.accept_invite")
    def test_accept_not_found(self, mock_accept, client, auth_headers):
        from app.exceptions import InviteNotFoundError

        inv_id = uuid4()
        mock_accept.side_effect = InviteNotFoundError(inv_id)

        response = client.post(
            f"/me/invites/{inv_id}:accept", headers=auth_headers
        )
        assert response.status_code == 404

    @patch("app.services.invite.InviteService.accept_invite")
    def test_accept_expired(self, mock_accept, client, auth_headers):
        from app.exceptions import InviteExpiredError

        mock_accept.side_effect = InviteExpiredError()
        response = client.post(
            f"/me/invites/{uuid4()}:accept", headers=auth_headers
        )
        assert response.status_code == 410

    @patch("app.services.invite.InviteService.accept_invite")
    def test_accept_not_actionable(self, mock_accept, client, auth_headers):
        from app.exceptions import InviteNotActionableError

        mock_accept.side_effect = InviteNotActionableError()
        response = client.post(
            f"/me/invites/{uuid4()}:accept", headers=auth_headers
        )
        assert response.status_code == 400

    @patch("app.services.invite.InviteService.accept_invite")
    def test_accept_already_used(self, mock_accept, client, auth_headers):
        from app.exceptions import InviteAlreadyUsedError

        mock_accept.side_effect = InviteAlreadyUsedError()
        response = client.post(
            f"/me/invites/{uuid4()}:accept", headers=auth_headers
        )
        assert response.status_code == 410


# ==================== Reject Invite ====================


class TestRejectInviteEndpoint:
    """Tests for POST /me/invites/{invite_id}:reject."""

    @patch("app.services.invite.InviteService.reject_invite")
    def test_reject_success(self, mock_reject, client, auth_headers):
        mock_reject.return_value = None

        response = client.post(
            f"/me/invites/{uuid4()}:reject", headers=auth_headers
        )
        assert response.status_code == 204

    @patch("app.services.invite.InviteService.reject_invite")
    def test_reject_not_found(self, mock_reject, client, auth_headers):
        from app.exceptions import InviteNotFoundError

        inv_id = uuid4()
        mock_reject.side_effect = InviteNotFoundError(inv_id)

        response = client.post(
            f"/me/invites/{inv_id}:reject", headers=auth_headers
        )
        assert response.status_code == 404

    @patch("app.services.invite.InviteService.reject_invite")
    def test_reject_not_actionable(self, mock_reject, client, auth_headers):
        from app.exceptions import InviteNotActionableError

        mock_reject.side_effect = InviteNotActionableError()
        response = client.post(
            f"/me/invites/{uuid4()}:reject", headers=auth_headers
        )
        assert response.status_code == 400

    @patch("app.services.invite.InviteService.reject_invite")
    def test_reject_expired(self, mock_reject, client, auth_headers):
        from app.exceptions import InviteExpiredError

        mock_reject.side_effect = InviteExpiredError()
        response = client.post(
            f"/me/invites/{uuid4()}:reject", headers=auth_headers
        )
        assert response.status_code == 410
