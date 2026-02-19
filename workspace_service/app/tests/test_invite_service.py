"""
Unit tests for InviteService - Workspace Invitation Logic.

Tests cover:
- Create invite (success, errors, idempotency)
- Accept invite (success, errors)
- Reject invite (success, errors)
- Cancel invite (owner only)
- Get my invites
- Expire old invites
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.invite import InviteService
from app.models.invite import WorkspaceInvite, InviteStatus
from app.models.member import MemberRole, MemberStatus, WorkspaceMember
from app.schemas.invite import InviteCreate
from app.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceAccessDeniedError,
    WorkspaceArchivedError,
    InviteNotFoundError,
    InviteExpiredError,
    InviteNotActionableError,
    InviteeNotFoundError,
    SelfInviteNotAllowedError,
    MemberAlreadyExistsError,
)


class TestCreateInvite:
    """Tests for InviteService.create_invite()"""

    def test_create_invite_success_read_role(
        self, invite_service, shared_workspace, owner_user, member_user
    ):
        """TC-B01: Successfully create invite with read role"""
        data = InviteCreate(email=member_user.email, role="read")
        
        invite, is_new = invite_service.create_invite(
            workspace_id=shared_workspace.id,
            owner_user_id=owner_user.id,
            data=data
        )
        
        assert is_new is True
        assert invite.workspace_id == shared_workspace.id
        assert invite.inviter_user_id == owner_user.id
        assert invite.invitee_user_id == member_user.id
        assert invite.invitee_email == member_user.email
        assert invite.role == MemberRole.READ
        assert invite.status == InviteStatus.PENDING
        assert invite.expires_at > datetime.utcnow()

    def test_create_invite_success_full_role(
        self, invite_service, shared_workspace, owner_user, member_user
    ):
        """Successfully create invite with full role"""
        data = InviteCreate(email=member_user.email, role="full")
        
        invite, is_new = invite_service.create_invite(
            workspace_id=shared_workspace.id,
            owner_user_id=owner_user.id,
            data=data
        )
        
        assert is_new is True
        assert invite.role == MemberRole.FULL

    def test_create_invite_nonexistent_user(
        self, invite_service, shared_workspace, owner_user
    ):
        """TC-B02: Fail to create invite for non-existent user"""
        data = InviteCreate(email="nonexistent@test.com", role="read")
        
        with pytest.raises(InviteeNotFoundError) as exc_info:
            invite_service.create_invite(
                workspace_id=shared_workspace.id,
                owner_user_id=owner_user.id,
                data=data
            )
        
        assert "nonexistent@test.com" in str(exc_info.value.detail)

    def test_create_invite_self_invite(
        self, invite_service, shared_workspace, owner_user
    ):
        """TC-B03: Fail when owner tries to invite themselves"""
        data = InviteCreate(email=owner_user.email, role="read")
        
        with pytest.raises(SelfInviteNotAllowedError):
            invite_service.create_invite(
                workspace_id=shared_workspace.id,
                owner_user_id=owner_user.id,
                data=data
            )

    def test_create_invite_already_member(
        self, invite_service, workspace_with_member, owner_user, member_user
    ):
        """TC-B04: Fail when invitee is already a member"""
        data = InviteCreate(email=member_user.email, role="read")
        
        with pytest.raises(MemberAlreadyExistsError):
            invite_service.create_invite(
                workspace_id=workspace_with_member.id,
                owner_user_id=owner_user.id,
                data=data
            )

    def test_create_invite_duplicate_pending_returns_existing(
        self, invite_service, pending_invite, owner_user, member_user
    ):
        """TC-B05: Return existing invite when duplicate pending exists (idempotent)"""
        data = InviteCreate(email=member_user.email, role="full")
        
        invite, is_new = invite_service.create_invite(
            workspace_id=pending_invite.workspace_id,
            owner_user_id=owner_user.id,
            data=data
        )
        
        assert is_new is False
        assert invite.id == pending_invite.id

    def test_create_invite_non_owner_fails(
        self, invite_service, workspace_with_member, member_user, other_user
    ):
        """TC-B06: Fail when non-owner tries to create invite"""
        data = InviteCreate(email=other_user.email, role="read")
        
        with pytest.raises(WorkspaceAccessDeniedError) as exc_info:
            invite_service.create_invite(
                workspace_id=workspace_with_member.id,
                owner_user_id=member_user.id,  # member_user is not owner
                data=data
            )
        
        assert "owner" in str(exc_info.value.detail).lower()

    def test_create_invite_archived_workspace(
        self, invite_service, archived_workspace, owner_user, member_user
    ):
        """TC-B07: Fail when workspace is archived"""
        data = InviteCreate(email=member_user.email, role="read")
        
        with pytest.raises(WorkspaceArchivedError):
            invite_service.create_invite(
                workspace_id=archived_workspace.id,
                owner_user_id=owner_user.id,
                data=data
            )

    def test_create_invite_nonexistent_workspace(
        self, invite_service, owner_user, member_user
    ):
        """Fail when workspace doesn't exist"""
        data = InviteCreate(email=member_user.email, role="read")
        fake_workspace_id = uuid4()
        
        with pytest.raises(WorkspaceNotFoundError):
            invite_service.create_invite(
                workspace_id=fake_workspace_id,
                owner_user_id=owner_user.id,
                data=data
            )

    def test_create_invite_after_rejection(
        self, invite_service, db_session, rejected_invite, owner_user, member_user
    ):
        """TC-B16: Allow creating new invite after rejection"""
        data = InviteCreate(email=member_user.email, role="full")
        
        invite, is_new = invite_service.create_invite(
            workspace_id=rejected_invite.workspace_id,
            owner_user_id=owner_user.id,
            data=data
        )
        
        assert is_new is True
        assert invite.id != rejected_invite.id
        assert invite.status == InviteStatus.PENDING

    def test_create_invite_after_cancellation(
        self, invite_service, db_session, canceled_invite, owner_user, member_user
    ):
        """Allow creating new invite after cancellation"""
        data = InviteCreate(email=member_user.email, role="read")
        
        invite, is_new = invite_service.create_invite(
            workspace_id=canceled_invite.workspace_id,
            owner_user_id=owner_user.id,
            data=data
        )
        
        assert is_new is True
        assert invite.id != canceled_invite.id

    def test_create_invite_for_removed_member(
        self, invite_service, shared_workspace, removed_member, owner_user, member_user
    ):
        """TC-B22: Allow re-inviting a removed member"""
        data = InviteCreate(email=member_user.email, role="full")
        
        # Removed member should not block invite creation
        invite, is_new = invite_service.create_invite(
            workspace_id=shared_workspace.id,
            owner_user_id=owner_user.id,
            data=data
        )
        
        assert is_new is True
        assert invite.invitee_user_id == member_user.id

    def test_create_invite_email_case_insensitive(
        self, invite_service, shared_workspace, owner_user, member_user
    ):
        """Email lookup should be case-insensitive"""
        data = InviteCreate(email="MEMBER@TEST.COM", role="read")
        
        invite, is_new = invite_service.create_invite(
            workspace_id=shared_workspace.id,
            owner_user_id=owner_user.id,
            data=data
        )
        
        assert is_new is True
        assert invite.invitee_user_id == member_user.id


class TestAcceptInvite:
    """Tests for InviteService.accept_invite()"""

    def test_accept_invite_success(
        self, invite_service, db_session, pending_invite, member_user
    ):
        """TC-B09: Successfully accept a pending invite"""
        invite = invite_service.accept_invite(
            invite_id=pending_invite.id,
            user_id=member_user.id
        )
        
        assert invite.status == InviteStatus.ACCEPTED
        assert invite.accepted_at is not None
        assert invite.responded_at is not None
        
        # Verify membership was created
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == pending_invite.workspace_id,
            WorkspaceMember.user_id == member_user.id,
            WorkspaceMember.status == MemberStatus.ACTIVE
        ).first()
        
        assert member is not None
        assert member.role == pending_invite.role

    def test_accept_invite_expired(
        self, invite_service, expired_invite, member_user
    ):
        """TC-B10: Fail to accept expired invite"""
        with pytest.raises(InviteExpiredError):
            invite_service.accept_invite(
                invite_id=expired_invite.id,
                user_id=member_user.id
            )

    def test_accept_invite_wrong_user(
        self, invite_service, pending_invite, other_user
    ):
        """TC-B11: Fail when different user tries to accept"""
        with pytest.raises(WorkspaceAccessDeniedError) as exc_info:
            invite_service.accept_invite(
                invite_id=pending_invite.id,
                user_id=other_user.id
            )
        
        assert "different user" in str(exc_info.value.detail)

    def test_accept_invite_already_accepted(
        self, invite_service, accepted_invite, member_user
    ):
        """TC-B12: Fail to accept already accepted invite"""
        with pytest.raises(InviteNotActionableError) as exc_info:
            invite_service.accept_invite(
                invite_id=accepted_invite.id,
                user_id=member_user.id
            )
        
        assert "accepted" in str(exc_info.value.detail)

    def test_accept_invite_not_found(
        self, invite_service, member_user
    ):
        """Fail when invite doesn't exist"""
        fake_invite_id = uuid4()
        
        with pytest.raises(InviteNotFoundError):
            invite_service.accept_invite(
                invite_id=fake_invite_id,
                user_id=member_user.id
            )

    def test_accept_invite_rejected_fails(
        self, invite_service, rejected_invite, member_user
    ):
        """Cannot accept a rejected invite"""
        with pytest.raises(InviteNotActionableError):
            invite_service.accept_invite(
                invite_id=rejected_invite.id,
                user_id=member_user.id
            )

    def test_accept_invite_canceled_fails(
        self, invite_service, canceled_invite, member_user
    ):
        """Cannot accept a canceled invite"""
        with pytest.raises(InviteNotActionableError):
            invite_service.accept_invite(
                invite_id=canceled_invite.id,
                user_id=member_user.id
            )

    def test_accept_invite_reactivates_removed_member(
        self, invite_service, db_session, shared_workspace, owner_user, member_user
    ):
        """Accepting invite reactivates a previously removed member"""
        # First create a removed member
        removed = WorkspaceMember(
            workspace_id=shared_workspace.id,
            user_id=member_user.id,
            role=MemberRole.READ,
            status=MemberStatus.REMOVED,
        )
        db_session.add(removed)
        db_session.commit()
        
        # Create an invite
        invite = WorkspaceInvite(
            id=uuid4(),
            workspace_id=shared_workspace.id,
            inviter_user_id=owner_user.id,
            invitee_user_id=member_user.id,
            invitee_email=member_user.email,
            role=MemberRole.FULL,
            status=InviteStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=3),
        )
        db_session.add(invite)
        db_session.commit()
        
        # Accept the invite
        accepted = invite_service.accept_invite(invite.id, member_user.id)
        
        assert accepted.status == InviteStatus.ACCEPTED
        
        # Verify member was reactivated with new role
        db_session.refresh(removed)
        assert removed.status == MemberStatus.ACTIVE
        assert removed.role == MemberRole.FULL


class TestRejectInvite:
    """Tests for InviteService.reject_invite()"""

    def test_reject_invite_success(
        self, invite_service, db_session, pending_invite, member_user
    ):
        """TC-B13: Successfully reject a pending invite"""
        invite_service.reject_invite(
            invite_id=pending_invite.id,
            user_id=member_user.id
        )
        
        db_session.refresh(pending_invite)
        assert pending_invite.status == InviteStatus.REJECTED
        assert pending_invite.responded_at is not None

    def test_reject_invite_wrong_user(
        self, invite_service, pending_invite, other_user
    ):
        """Fail when different user tries to reject"""
        with pytest.raises(WorkspaceAccessDeniedError):
            invite_service.reject_invite(
                invite_id=pending_invite.id,
                user_id=other_user.id
            )

    def test_reject_invite_expired(
        self, invite_service, expired_invite, member_user
    ):
        """Fail to reject expired invite"""
        with pytest.raises(InviteExpiredError):
            invite_service.reject_invite(
                invite_id=expired_invite.id,
                user_id=member_user.id
            )

    def test_reject_invite_not_found(
        self, invite_service, member_user
    ):
        """Fail when invite doesn't exist"""
        with pytest.raises(InviteNotFoundError):
            invite_service.reject_invite(
                invite_id=uuid4(),
                user_id=member_user.id
            )

    def test_reject_invite_already_accepted(
        self, invite_service, accepted_invite, member_user
    ):
        """Cannot reject already accepted invite"""
        with pytest.raises(InviteNotActionableError):
            invite_service.reject_invite(
                invite_id=accepted_invite.id,
                user_id=member_user.id
            )


class TestCancelInvite:
    """Tests for InviteService.cancel_invite()"""

    def test_cancel_invite_success(
        self, invite_service, db_session, pending_invite, owner_user
    ):
        """TC-B14: Successfully cancel a pending invite (owner)"""
        invite_service.cancel_invite(
            workspace_id=pending_invite.workspace_id,
            invite_id=pending_invite.id,
            user_id=owner_user.id
        )
        
        db_session.refresh(pending_invite)
        assert pending_invite.status == InviteStatus.CANCELED
        assert pending_invite.responded_at is not None

    def test_cancel_invite_non_owner_fails(
        self, invite_service, db_session, shared_workspace, pending_invite, member_user
    ):
        """TC-B15: Non-owner cannot cancel invite"""
        # Add member_user as a FULL member (not owner)
        member = WorkspaceMember(
            workspace_id=shared_workspace.id,
            user_id=member_user.id,
            role=MemberRole.FULL,
            status=MemberStatus.ACTIVE,
        )
        db_session.add(member)
        db_session.commit()
        
        # Create another invite to cancel
        other_invite = WorkspaceInvite(
            id=uuid4(),
            workspace_id=shared_workspace.id,
            inviter_user_id=1,  # owner
            invitee_user_id=3,  # other_user
            invitee_email="other@test.com",
            role=MemberRole.READ,
            status=InviteStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=3),
        )
        db_session.add(other_invite)
        db_session.commit()
        
        with pytest.raises(WorkspaceAccessDeniedError):
            invite_service.cancel_invite(
                workspace_id=shared_workspace.id,
                invite_id=other_invite.id,
                user_id=member_user.id  # member, not owner
            )

    def test_cancel_invite_not_found(
        self, invite_service, shared_workspace, owner_user
    ):
        """Fail when invite doesn't exist"""
        with pytest.raises(InviteNotFoundError):
            invite_service.cancel_invite(
                workspace_id=shared_workspace.id,
                invite_id=uuid4(),
                user_id=owner_user.id
            )

    def test_cancel_invite_already_accepted(
        self, invite_service, accepted_invite, owner_user
    ):
        """Cannot cancel already accepted invite"""
        from app.exceptions import InviteAlreadyUsedError
        
        with pytest.raises(InviteAlreadyUsedError):
            invite_service.cancel_invite(
                workspace_id=accepted_invite.workspace_id,
                invite_id=accepted_invite.id,
                user_id=owner_user.id
            )


class TestGetMyInvites:
    """Tests for InviteService.get_my_invites()"""

    def test_get_my_invites_pending_only(
        self, invite_service, pending_invite, member_user
    ):
        """TC-B08: Get only pending invites by default"""
        invites = invite_service.get_my_invites(user_id=member_user.id)
        
        assert len(invites) == 1
        assert invites[0].id == pending_invite.id
        assert invites[0].workspace_name is not None
        assert invites[0].inviter_email is not None

    def test_get_my_invites_empty(
        self, invite_service, other_user
    ):
        """Return empty list when no invites"""
        invites = invite_service.get_my_invites(user_id=other_user.id)
        assert len(invites) == 0

    def test_get_my_invites_include_all(
        self, invite_service, db_session, shared_workspace, owner_user, member_user
    ):
        """Include all statuses when include_all=True"""
        # Create invites with different statuses
        pending = WorkspaceInvite(
            id=uuid4(),
            workspace_id=shared_workspace.id,
            inviter_user_id=owner_user.id,
            invitee_user_id=member_user.id,
            invitee_email=member_user.email,
            role=MemberRole.READ,
            status=InviteStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=3),
        )
        rejected = WorkspaceInvite(
            id=uuid4(),
            workspace_id=shared_workspace.id,
            inviter_user_id=owner_user.id,
            invitee_user_id=member_user.id,
            invitee_email=member_user.email,
            role=MemberRole.READ,
            status=InviteStatus.REJECTED,
            expires_at=datetime.utcnow() + timedelta(days=3),
        )
        db_session.add_all([pending, rejected])
        db_session.commit()
        
        # Without include_all - only pending
        pending_only = invite_service.get_my_invites(user_id=member_user.id, include_all=False)
        assert len(pending_only) == 1
        
        # With include_all - both
        all_invites = invite_service.get_my_invites(user_id=member_user.id, include_all=True)
        assert len(all_invites) == 2

    def test_get_my_invites_response_enriched(
        self, invite_service, pending_invite, member_user
    ):
        """Verify response contains enriched data"""
        invites = invite_service.get_my_invites(user_id=member_user.id)
        
        assert len(invites) == 1
        inv = invites[0]
        
        # Check all expected fields are populated
        assert inv.id == pending_invite.id
        assert inv.workspace_id == pending_invite.workspace_id
        assert inv.workspace_name == "Test Workspace"
        assert inv.inviter_user_id == pending_invite.inviter_user_id
        assert inv.inviter_email == "owner@test.com"
        assert inv.role == pending_invite.role
        assert inv.status == InviteStatus.PENDING
        assert inv.expires_at is not None


class TestGetWorkspaceInvites:
    """Tests for InviteService.get_workspace_invites()"""

    def test_get_workspace_invites_owner_only(
        self, invite_service, pending_invite, owner_user
    ):
        """Owner can view workspace invites"""
        invites = invite_service.get_workspace_invites(
            workspace_id=pending_invite.workspace_id,
            user_id=owner_user.id
        )
        
        assert len(invites) == 1
        assert invites[0].id == pending_invite.id

    def test_get_workspace_invites_non_owner_fails(
        self, invite_service, workspace_with_member, member_user
    ):
        """Non-owner cannot view workspace invites"""
        with pytest.raises(WorkspaceAccessDeniedError):
            invite_service.get_workspace_invites(
                workspace_id=workspace_with_member.id,
                user_id=member_user.id
            )

    def test_get_workspace_invites_filter_by_status(
        self, invite_service, db_session, shared_workspace, owner_user, member_user
    ):
        """Filter invites by status"""
        # Create invites with different statuses
        pending = WorkspaceInvite(
            id=uuid4(),
            workspace_id=shared_workspace.id,
            inviter_user_id=owner_user.id,
            invitee_user_id=member_user.id,
            invitee_email=member_user.email,
            role=MemberRole.READ,
            status=InviteStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=3),
        )
        accepted = WorkspaceInvite(
            id=uuid4(),
            workspace_id=shared_workspace.id,
            inviter_user_id=owner_user.id,
            invitee_user_id=3,
            invitee_email="other@test.com",
            role=MemberRole.READ,
            status=InviteStatus.ACCEPTED,
            expires_at=datetime.utcnow() + timedelta(days=3),
        )
        db_session.add_all([pending, accepted])
        db_session.commit()
        
        # Filter by PENDING
        pending_invites = invite_service.get_workspace_invites(
            workspace_id=shared_workspace.id,
            user_id=owner_user.id,
            status_filter=InviteStatus.PENDING
        )
        assert len(pending_invites) == 1
        assert pending_invites[0].status == InviteStatus.PENDING
        
        # Filter by ACCEPTED
        accepted_invites = invite_service.get_workspace_invites(
            workspace_id=shared_workspace.id,
            user_id=owner_user.id,
            status_filter=InviteStatus.ACCEPTED
        )
        assert len(accepted_invites) == 1
        assert accepted_invites[0].status == InviteStatus.ACCEPTED


class TestExpireOldInvites:
    """Tests for InviteService.expire_old_invites()"""

    def test_expire_old_invites(
        self, invite_service, db_session, expired_invite
    ):
        """Mark expired invites as EXPIRED"""
        # Initially the expired invite is still PENDING
        assert expired_invite.status == InviteStatus.PENDING
        
        count = invite_service.expire_old_invites()
        
        assert count == 1
        
        db_session.refresh(expired_invite)
        assert expired_invite.status == InviteStatus.EXPIRED

    def test_expire_old_invites_no_expired(
        self, invite_service, pending_invite
    ):
        """No change when no invites are expired"""
        count = invite_service.expire_old_invites()
        assert count == 0
        
        assert pending_invite.status == InviteStatus.PENDING

    def test_expire_old_invites_skips_non_pending(
        self, invite_service, db_session, shared_workspace, owner_user
    ):
        """Only expire PENDING invites"""
        # Create an accepted invite that's past expiration
        old_accepted = WorkspaceInvite(
            id=uuid4(),
            workspace_id=shared_workspace.id,
            inviter_user_id=owner_user.id,
            invitee_user_id=2,
            invitee_email="member@test.com",
            role=MemberRole.READ,
            status=InviteStatus.ACCEPTED,  # Already accepted
            expires_at=datetime.utcnow() - timedelta(days=10),  # Expired
        )
        db_session.add(old_accepted)
        db_session.commit()
        
        count = invite_service.expire_old_invites()
        
        assert count == 0
        db_session.refresh(old_accepted)
        assert old_accepted.status == InviteStatus.ACCEPTED  # Unchanged
