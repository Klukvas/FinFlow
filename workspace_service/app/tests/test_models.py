"""
Unit tests for SQLAlchemy Models.

Tests cover:
- WorkspaceInvite model properties
- WorkspaceMember model properties
- Workspace model properties
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.invite import WorkspaceInvite, InviteStatus
from app.models.member import WorkspaceMember, MemberRole, MemberStatus
from app.models.workspace import Workspace, WorkspaceType


class TestWorkspaceInviteModel:
    """Tests for WorkspaceInvite model properties"""

    def test_is_pending_true(self, db_session, shared_workspace, owner_user, member_user):
        """is_pending returns True for pending invites"""
        invite = WorkspaceInvite(
            id=uuid4(),
            workspace_id=shared_workspace.id,
            inviter_user_id=owner_user.id,
            invitee_user_id=member_user.id,
            invitee_email=member_user.email,
            role=MemberRole.READ,
            status=InviteStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(days=3),
        )
        db_session.add(invite)
        db_session.commit()
        
        assert invite.is_pending is True

    def test_is_pending_false_accepted(self, db_session, accepted_invite):
        """is_pending returns False for accepted invites"""
        assert accepted_invite.is_pending is False

    def test_is_pending_false_rejected(self, db_session, rejected_invite):
        """is_pending returns False for rejected invites"""
        assert rejected_invite.is_pending is False

    def test_is_expired_true(self, db_session, expired_invite):
        """is_expired returns True when expires_at is in the past"""
        assert expired_invite.is_expired is True

    def test_is_expired_false(self, db_session, pending_invite):
        """is_expired returns False when expires_at is in the future"""
        assert pending_invite.is_expired is False

    def test_is_actionable_pending_not_expired(self, db_session, pending_invite):
        """is_actionable returns True for pending, non-expired invites"""
        assert pending_invite.is_actionable is True

    def test_is_actionable_false_expired(self, db_session, expired_invite):
        """is_actionable returns False for expired invites"""
        assert expired_invite.is_actionable is False

    def test_is_actionable_false_accepted(self, db_session, accepted_invite):
        """is_actionable returns False for accepted invites"""
        assert accepted_invite.is_actionable is False

    def test_is_actionable_false_rejected(self, db_session, rejected_invite):
        """is_actionable returns False for rejected invites"""
        assert rejected_invite.is_actionable is False

    def test_is_actionable_false_canceled(self, db_session, canceled_invite):
        """is_actionable returns False for canceled invites"""
        assert canceled_invite.is_actionable is False

    def test_can_be_reinvited_expired(self, db_session, shared_workspace, owner_user, member_user):
        """can_be_reinvited returns True for expired invites"""
        invite = WorkspaceInvite(
            id=uuid4(),
            workspace_id=shared_workspace.id,
            inviter_user_id=owner_user.id,
            invitee_user_id=member_user.id,
            invitee_email=member_user.email,
            role=MemberRole.READ,
            status=InviteStatus.EXPIRED,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        db_session.add(invite)
        db_session.commit()
        
        assert invite.can_be_reinvited() is True

    def test_can_be_reinvited_rejected(self, db_session, rejected_invite):
        """can_be_reinvited returns True for rejected invites"""
        assert rejected_invite.can_be_reinvited() is True

    def test_can_be_reinvited_canceled(self, db_session, canceled_invite):
        """can_be_reinvited returns True for canceled invites"""
        assert canceled_invite.can_be_reinvited() is True

    def test_can_be_reinvited_false_pending(self, db_session, pending_invite):
        """can_be_reinvited returns False for pending invites"""
        assert pending_invite.can_be_reinvited() is False

    def test_can_be_reinvited_false_accepted(self, db_session, accepted_invite):
        """can_be_reinvited returns False for accepted invites"""
        assert accepted_invite.can_be_reinvited() is False


class TestWorkspaceMemberModel:
    """Tests for WorkspaceMember model properties"""

    def test_is_active_true(self, db_session, shared_workspace, owner_user):
        """is_active returns True for active members"""
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == shared_workspace.id,
            WorkspaceMember.user_id == owner_user.id
        ).first()
        
        assert member.is_active is True

    def test_is_active_false_removed(self, db_session, removed_member):
        """is_active returns False for removed members"""
        assert removed_member.is_active is False

    def test_is_active_false_left(self, db_session, shared_workspace, member_user):
        """is_active returns False for members who left"""
        member = WorkspaceMember(
            workspace_id=shared_workspace.id,
            user_id=member_user.id,
            role=MemberRole.FULL,
            status=MemberStatus.LEFT,
        )
        db_session.add(member)
        db_session.commit()
        
        assert member.is_active is False

    def test_is_owner_true(self, db_session, shared_workspace, owner_user):
        """is_owner returns True for owner"""
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == shared_workspace.id,
            WorkspaceMember.user_id == owner_user.id
        ).first()
        
        assert member.is_owner is True

    def test_is_owner_false_full_member(self, db_session, workspace_with_member, member_user):
        """is_owner returns False for full members"""
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_with_member.id,
            WorkspaceMember.user_id == member_user.id
        ).first()
        
        assert member.is_owner is False

    def test_can_manage_members_owner(self, db_session, shared_workspace, owner_user):
        """can_manage_members returns True for owner"""
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == shared_workspace.id,
            WorkspaceMember.user_id == owner_user.id
        ).first()
        
        assert member.can_manage_members() is True

    def test_can_manage_members_full(self, db_session, workspace_with_member, member_user):
        """can_manage_members returns False for full members"""
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_with_member.id,
            WorkspaceMember.user_id == member_user.id
        ).first()
        
        assert member.can_manage_members() is False

    def test_can_invite_owner(self, db_session, shared_workspace, owner_user):
        """can_invite returns True for owner"""
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == shared_workspace.id,
            WorkspaceMember.user_id == owner_user.id
        ).first()
        
        assert member.can_invite() is True

    def test_can_invite_full(self, db_session, workspace_with_member, member_user):
        """can_invite returns False for full members"""
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_with_member.id,
            WorkspaceMember.user_id == member_user.id
        ).first()
        
        assert member.can_invite() is False

    def test_can_write_owner(self, db_session, shared_workspace, owner_user):
        """can_write returns True for owner"""
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == shared_workspace.id,
            WorkspaceMember.user_id == owner_user.id
        ).first()
        
        assert member.can_write() is True

    def test_can_write_full(self, db_session, workspace_with_member, member_user):
        """can_write returns True for full members"""
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_with_member.id,
            WorkspaceMember.user_id == member_user.id
        ).first()
        
        assert member.can_write() is True

    def test_can_write_read(self, db_session, workspace_with_read_member, member_user):
        """can_write returns False for read-only members"""
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_with_read_member.id,
            WorkspaceMember.user_id == member_user.id
        ).first()
        
        assert member.can_write() is False

    def test_can_read_all_active(self, db_session, workspace_with_read_member, member_user):
        """can_read returns True for all active members"""
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_with_read_member.id,
            WorkspaceMember.user_id == member_user.id
        ).first()
        
        assert member.can_read() is True

    def test_can_read_removed(self, db_session, removed_member):
        """can_read returns False for removed members"""
        assert removed_member.can_read() is False


class TestWorkspaceModel:
    """Tests for Workspace model properties"""

    def test_is_archived_false(self, db_session, shared_workspace):
        """is_archived returns False for active workspaces"""
        assert shared_workspace.is_archived is False

    def test_is_archived_true(self, db_session, archived_workspace):
        """is_archived returns True for archived workspaces"""
        assert archived_workspace.is_archived is True


class TestMemberRoleEnum:
    """Tests for MemberRole enum values"""

    def test_role_values(self):
        """Verify role enum values"""
        assert MemberRole.OWNER.value == "owner"
        assert MemberRole.FULL.value == "full"
        assert MemberRole.READ.value == "read"

    def test_role_is_string(self):
        """Roles are string enums"""
        assert isinstance(MemberRole.OWNER.value, str)
        assert isinstance(MemberRole.FULL.value, str)
        assert isinstance(MemberRole.READ.value, str)


class TestInviteStatusEnum:
    """Tests for InviteStatus enum values"""

    def test_status_values(self):
        """Verify status enum values"""
        assert InviteStatus.PENDING.value == "pending"
        assert InviteStatus.ACCEPTED.value == "accepted"
        assert InviteStatus.REJECTED.value == "rejected"
        assert InviteStatus.EXPIRED.value == "expired"
        assert InviteStatus.CANCELED.value == "canceled"


class TestMemberStatusEnum:
    """Tests for MemberStatus enum values"""

    def test_status_values(self):
        """Verify status enum values"""
        assert MemberStatus.ACTIVE.value == "active"
        assert MemberStatus.LEFT.value == "left"
        assert MemberStatus.REMOVED.value == "removed"


class TestWorkspaceTypeEnum:
    """Tests for WorkspaceType enum values"""

    def test_type_values(self):
        """Verify type enum values"""
        assert WorkspaceType.PERSONAL.value == "personal"
        assert WorkspaceType.SHARED.value == "shared"
