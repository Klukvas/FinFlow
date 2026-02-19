"""
Unit tests for WorkspaceService - Member Management Logic.

Tests cover:
- Get members
- Update member role
- Remove member
- Add member (internal)
- Authorization checks
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.services.workspace import WorkspaceService
from app.models.member import MemberRole, MemberStatus, WorkspaceMember
from app.models.workspace import Workspace, WorkspaceType
from app.schemas.member import MemberRoleUpdate
from app.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceAccessDeniedError,
    WorkspaceArchivedError,
    MemberNotFoundError,
    MemberAlreadyExistsError,
    InvalidRoleChangeError,
    OwnerCannotLeaveError,
    PersonalWorkspaceProtectedError,
)


class TestGetMembers:
    """Tests for WorkspaceService.get_members()"""

    def test_get_members_success(
        self, workspace_service, workspace_with_member, owner_user
    ):
        """TC-F07: Get all active members"""
        members = workspace_service.get_members(
            workspace_id=workspace_with_member.id,
            user_id=owner_user.id
        )
        
        assert len(members) == 2  # owner + member
        
        # Verify member data is enriched
        for member in members:
            assert member.email is not None

    def test_get_members_any_member_can_view(
        self, workspace_service, workspace_with_member, member_user
    ):
        """Any member can view the member list"""
        members = workspace_service.get_members(
            workspace_id=workspace_with_member.id,
            user_id=member_user.id
        )
        
        assert len(members) == 2

    def test_get_members_non_member_denied(
        self, workspace_service, shared_workspace, other_user
    ):
        """Non-member cannot view members"""
        with pytest.raises(WorkspaceAccessDeniedError):
            workspace_service.get_members(
                workspace_id=shared_workspace.id,
                user_id=other_user.id
            )

    def test_get_members_excludes_inactive(
        self, workspace_service, db_session, shared_workspace, owner_user, member_user
    ):
        """Only return active members"""
        # Add a removed member
        removed = WorkspaceMember(
            workspace_id=shared_workspace.id,
            user_id=member_user.id,
            role=MemberRole.READ,
            status=MemberStatus.REMOVED,
        )
        db_session.add(removed)
        db_session.commit()
        
        members = workspace_service.get_members(
            workspace_id=shared_workspace.id,
            user_id=owner_user.id
        )
        
        # Should only return owner, not the removed member
        assert len(members) == 1
        assert members[0].user_id == owner_user.id


class TestUpdateMemberRole:
    """Tests for WorkspaceService.update_member_role()"""

    def test_update_member_role_to_full(
        self, workspace_service, db_session, workspace_with_read_member, owner_user, member_user
    ):
        """TC-B18: Owner can change member role to full"""
        data = MemberRoleUpdate(role="full")
        
        updated = workspace_service.update_member_role(
            workspace_id=workspace_with_read_member.id,
            target_user_id=member_user.id,
            user_id=owner_user.id,
            data=data
        )
        
        assert updated.role == MemberRole.FULL

    def test_update_member_role_to_read(
        self, workspace_service, workspace_with_member, owner_user, member_user
    ):
        """Owner can change member role to read"""
        data = MemberRoleUpdate(role="read")
        
        updated = workspace_service.update_member_role(
            workspace_id=workspace_with_member.id,
            target_user_id=member_user.id,
            user_id=owner_user.id,
            data=data
        )
        
        assert updated.role == MemberRole.READ

    def test_update_member_role_non_owner_fails(
        self, workspace_service, db_session, shared_workspace, owner_user, member_user, other_user
    ):
        """TC-B19: Non-owner cannot change roles"""
        # Add member_user as FULL member
        member = WorkspaceMember(
            workspace_id=shared_workspace.id,
            user_id=member_user.id,
            role=MemberRole.FULL,
            status=MemberStatus.ACTIVE,
        )
        # Add other_user as READ member
        other_member = WorkspaceMember(
            workspace_id=shared_workspace.id,
            user_id=other_user.id,
            role=MemberRole.READ,
            status=MemberStatus.ACTIVE,
        )
        db_session.add_all([member, other_member])
        db_session.commit()
        
        data = MemberRoleUpdate(role="full")
        
        with pytest.raises(WorkspaceAccessDeniedError) as exc_info:
            workspace_service.update_member_role(
                workspace_id=shared_workspace.id,
                target_user_id=other_user.id,
                user_id=member_user.id,  # FULL member, not owner
                data=data
            )
        
        assert "owner" in str(exc_info.value.detail).lower()

    def test_update_member_role_cannot_change_owner(
        self, workspace_service, workspace_with_member, owner_user, member_user
    ):
        """Cannot change owner's role"""
        data = MemberRoleUpdate(role="read")
        
        with pytest.raises(InvalidRoleChangeError) as exc_info:
            workspace_service.update_member_role(
                workspace_id=workspace_with_member.id,
                target_user_id=owner_user.id,  # Target is the owner
                user_id=owner_user.id,
                data=data
            )
        
        assert "owner" in str(exc_info.value.detail).lower()

    def test_update_member_role_member_not_found(
        self, workspace_service, shared_workspace, owner_user
    ):
        """Fail when target member doesn't exist"""
        data = MemberRoleUpdate(role="full")
        
        with pytest.raises(MemberNotFoundError):
            workspace_service.update_member_role(
                workspace_id=shared_workspace.id,
                target_user_id=999,  # Non-existent user
                user_id=owner_user.id,
                data=data
            )

    def test_update_member_role_archived_workspace(
        self, workspace_service, db_session, archived_workspace, owner_user, member_user
    ):
        """Cannot change roles in archived workspace"""
        # Add a member to archived workspace
        member = WorkspaceMember(
            workspace_id=archived_workspace.id,
            user_id=member_user.id,
            role=MemberRole.READ,
            status=MemberStatus.ACTIVE,
        )
        db_session.add(member)
        db_session.commit()
        
        data = MemberRoleUpdate(role="full")
        
        with pytest.raises(WorkspaceArchivedError):
            workspace_service.update_member_role(
                workspace_id=archived_workspace.id,
                target_user_id=member_user.id,
                user_id=owner_user.id,
                data=data
            )


class TestRemoveMember:
    """Tests for WorkspaceService.remove_member()"""

    def test_remove_member_success(
        self, workspace_service, db_session, workspace_with_member, owner_user, member_user
    ):
        """TC-B20: Owner can remove a member"""
        workspace_service.remove_member(
            workspace_id=workspace_with_member.id,
            target_user_id=member_user.id,
            user_id=owner_user.id
        )
        
        # Verify member is marked as removed
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_with_member.id,
            WorkspaceMember.user_id == member_user.id
        ).first()
        
        assert member.status == MemberStatus.REMOVED

    def test_remove_member_cannot_remove_owner(
        self, workspace_service, shared_workspace, owner_user
    ):
        """TC-B21: Cannot remove the workspace owner"""
        with pytest.raises(InvalidRoleChangeError) as exc_info:
            workspace_service.remove_member(
                workspace_id=shared_workspace.id,
                target_user_id=owner_user.id,
                user_id=owner_user.id
            )
        
        assert "owner" in str(exc_info.value.detail).lower()

    def test_remove_member_non_owner_fails(
        self, workspace_service, db_session, shared_workspace, owner_user, member_user, other_user
    ):
        """Non-owner cannot remove members"""
        # Add member_user as FULL member
        member = WorkspaceMember(
            workspace_id=shared_workspace.id,
            user_id=member_user.id,
            role=MemberRole.FULL,
            status=MemberStatus.ACTIVE,
        )
        # Add other_user as READ member
        other_member = WorkspaceMember(
            workspace_id=shared_workspace.id,
            user_id=other_user.id,
            role=MemberRole.READ,
            status=MemberStatus.ACTIVE,
        )
        db_session.add_all([member, other_member])
        db_session.commit()
        
        with pytest.raises(WorkspaceAccessDeniedError):
            workspace_service.remove_member(
                workspace_id=shared_workspace.id,
                target_user_id=other_user.id,
                user_id=member_user.id  # FULL member, not owner
            )

    def test_remove_member_not_found(
        self, workspace_service, shared_workspace, owner_user
    ):
        """Fail when target member doesn't exist"""
        with pytest.raises(MemberNotFoundError):
            workspace_service.remove_member(
                workspace_id=shared_workspace.id,
                target_user_id=999,
                user_id=owner_user.id
            )

    def test_remove_member_archived_workspace(
        self, workspace_service, db_session, archived_workspace, owner_user, member_user
    ):
        """Cannot remove members from archived workspace"""
        member = WorkspaceMember(
            workspace_id=archived_workspace.id,
            user_id=member_user.id,
            role=MemberRole.READ,
            status=MemberStatus.ACTIVE,
        )
        db_session.add(member)
        db_session.commit()
        
        with pytest.raises(WorkspaceArchivedError):
            workspace_service.remove_member(
                workspace_id=archived_workspace.id,
                target_user_id=member_user.id,
                user_id=owner_user.id
            )


class TestAddMember:
    """Tests for WorkspaceService.add_member()"""

    def test_add_member_success(
        self, workspace_service, db_session, shared_workspace, member_user
    ):
        """Successfully add a new member"""
        member = workspace_service.add_member(
            workspace_id=shared_workspace.id,
            new_user_id=member_user.id,
            role=MemberRole.FULL
        )
        
        assert member.user_id == member_user.id
        assert member.role == MemberRole.FULL
        assert member.status == MemberStatus.ACTIVE

    def test_add_member_default_read_role(
        self, workspace_service, shared_workspace, member_user
    ):
        """Default role is READ"""
        member = workspace_service.add_member(
            workspace_id=shared_workspace.id,
            new_user_id=member_user.id
        )
        
        assert member.role == MemberRole.READ

    def test_add_member_already_active_fails(
        self, workspace_service, workspace_with_member, member_user
    ):
        """Cannot add already active member"""
        with pytest.raises(MemberAlreadyExistsError):
            workspace_service.add_member(
                workspace_id=workspace_with_member.id,
                new_user_id=member_user.id,
                role=MemberRole.READ
            )

    def test_add_member_reactivates_removed(
        self, workspace_service, db_session, shared_workspace, member_user
    ):
        """Reactivate previously removed member"""
        # First add and remove
        removed = WorkspaceMember(
            workspace_id=shared_workspace.id,
            user_id=member_user.id,
            role=MemberRole.READ,
            status=MemberStatus.REMOVED,
        )
        db_session.add(removed)
        db_session.commit()
        
        # Re-add with different role
        reactivated = workspace_service.add_member(
            workspace_id=shared_workspace.id,
            new_user_id=member_user.id,
            role=MemberRole.FULL
        )
        
        assert reactivated.status == MemberStatus.ACTIVE
        assert reactivated.role == MemberRole.FULL

    def test_add_member_reactivates_left(
        self, workspace_service, db_session, shared_workspace, member_user
    ):
        """Reactivate member who left"""
        left = WorkspaceMember(
            workspace_id=shared_workspace.id,
            user_id=member_user.id,
            role=MemberRole.FULL,
            status=MemberStatus.LEFT,
        )
        db_session.add(left)
        db_session.commit()
        
        reactivated = workspace_service.add_member(
            workspace_id=shared_workspace.id,
            new_user_id=member_user.id,
            role=MemberRole.READ
        )
        
        assert reactivated.status == MemberStatus.ACTIVE
        assert reactivated.role == MemberRole.READ


class TestLeaveWorkspace:
    """Tests for WorkspaceService.leave_workspace()"""

    def test_leave_workspace_success(
        self, workspace_service, db_session, workspace_with_member, member_user
    ):
        """Member can leave workspace"""
        workspace_service.leave_workspace(
            workspace_id=workspace_with_member.id,
            user_id=member_user.id
        )
        
        member = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_with_member.id,
            WorkspaceMember.user_id == member_user.id
        ).first()
        
        assert member.status == MemberStatus.LEFT

    def test_leave_workspace_owner_fails(
        self, workspace_service, shared_workspace, owner_user
    ):
        """Owner cannot leave without transferring ownership"""
        with pytest.raises(OwnerCannotLeaveError):
            workspace_service.leave_workspace(
                workspace_id=shared_workspace.id,
                user_id=owner_user.id
            )

    def test_leave_personal_workspace_fails(
        self, workspace_service, personal_workspace, owner_user
    ):
        """Cannot leave personal workspace"""
        with pytest.raises(PersonalWorkspaceProtectedError):
            workspace_service.leave_workspace(
                workspace_id=personal_workspace.id,
                user_id=owner_user.id
            )

    def test_leave_archived_workspace_fails(
        self, workspace_service, db_session, archived_workspace, member_user
    ):
        """Cannot leave archived workspace"""
        member = WorkspaceMember(
            workspace_id=archived_workspace.id,
            user_id=member_user.id,
            role=MemberRole.READ,
            status=MemberStatus.ACTIVE,
        )
        db_session.add(member)
        db_session.commit()
        
        with pytest.raises(WorkspaceArchivedError):
            workspace_service.leave_workspace(
                workspace_id=archived_workspace.id,
                user_id=member_user.id
            )


class TestAuthorization:
    """Tests for WorkspaceService authorization methods"""

    def test_authorize_owner_has_all_access(
        self, workspace_service, shared_workspace, owner_user
    ):
        """Owner has access to all roles"""
        assert workspace_service.authorize(
            shared_workspace.id, owner_user.id, MemberRole.OWNER
        ) is True
        assert workspace_service.authorize(
            shared_workspace.id, owner_user.id, MemberRole.FULL
        ) is True
        assert workspace_service.authorize(
            shared_workspace.id, owner_user.id, MemberRole.READ
        ) is True

    def test_authorize_full_member(
        self, workspace_service, workspace_with_member, member_user
    ):
        """FULL member has write and read access"""
        assert workspace_service.authorize(
            workspace_with_member.id, member_user.id, MemberRole.OWNER
        ) is False
        assert workspace_service.authorize(
            workspace_with_member.id, member_user.id, MemberRole.FULL
        ) is True
        assert workspace_service.authorize(
            workspace_with_member.id, member_user.id, MemberRole.READ
        ) is True

    def test_authorize_read_member(
        self, workspace_service, workspace_with_read_member, member_user
    ):
        """READ member has only read access"""
        assert workspace_service.authorize(
            workspace_with_read_member.id, member_user.id, MemberRole.OWNER
        ) is False
        assert workspace_service.authorize(
            workspace_with_read_member.id, member_user.id, MemberRole.FULL
        ) is False
        assert workspace_service.authorize(
            workspace_with_read_member.id, member_user.id, MemberRole.READ
        ) is True

    def test_authorize_non_member_denied(
        self, workspace_service, shared_workspace, other_user
    ):
        """Non-member has no access"""
        assert workspace_service.authorize(
            shared_workspace.id, other_user.id, MemberRole.READ
        ) is False

    def test_authorize_removed_member_denied(
        self, workspace_service, shared_workspace, removed_member, member_user
    ):
        """Removed member has no access"""
        assert workspace_service.authorize(
            shared_workspace.id, member_user.id, MemberRole.READ
        ) is False

    def test_get_user_role(
        self, workspace_service, workspace_with_member, owner_user, member_user
    ):
        """Get user's role in workspace"""
        assert workspace_service.get_user_role(
            workspace_with_member.id, owner_user.id
        ) == MemberRole.OWNER
        
        assert workspace_service.get_user_role(
            workspace_with_member.id, member_user.id
        ) == MemberRole.FULL

    def test_get_user_role_non_member(
        self, workspace_service, shared_workspace, other_user
    ):
        """Non-member returns None"""
        assert workspace_service.get_user_role(
            shared_workspace.id, other_user.id
        ) is None


class TestTransferOwnership:
    """Tests for WorkspaceService.transfer_ownership()"""

    def test_transfer_ownership_success(
        self, workspace_service, db_session, workspace_with_member, owner_user, member_user
    ):
        """Successfully transfer ownership"""
        workspace = workspace_service.transfer_ownership(
            workspace_id=workspace_with_member.id,
            new_owner_id=member_user.id,
            user_id=owner_user.id
        )
        
        assert workspace.owner_user_id == member_user.id
        
        # Check roles were updated
        old_owner = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_with_member.id,
            WorkspaceMember.user_id == owner_user.id
        ).first()
        assert old_owner.role == MemberRole.FULL
        
        new_owner = db_session.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_with_member.id,
            WorkspaceMember.user_id == member_user.id
        ).first()
        assert new_owner.role == MemberRole.OWNER

    def test_transfer_ownership_non_owner_fails(
        self, workspace_service, workspace_with_member, owner_user, member_user
    ):
        """Only owner can transfer ownership"""
        # member_user tries to transfer ownership to owner_user (themselves)
        # This should fail because member_user is not the owner
        with pytest.raises(WorkspaceAccessDeniedError):
            workspace_service.transfer_ownership(
                workspace_id=workspace_with_member.id,
                new_owner_id=owner_user.id,  # Transfer to existing member
                user_id=member_user.id  # Non-owner attempting transfer
            )

    def test_transfer_ownership_to_non_member_fails(
        self, workspace_service, shared_workspace, owner_user, other_user
    ):
        """Cannot transfer to non-member"""
        with pytest.raises(MemberNotFoundError):
            workspace_service.transfer_ownership(
                workspace_id=shared_workspace.id,
                new_owner_id=other_user.id,
                user_id=owner_user.id
            )

    def test_transfer_ownership_personal_workspace_fails(
        self, workspace_service, personal_workspace, owner_user, member_user
    ):
        """Cannot transfer personal workspace ownership"""
        with pytest.raises(PersonalWorkspaceProtectedError):
            workspace_service.transfer_ownership(
                workspace_id=personal_workspace.id,
                new_owner_id=member_user.id,
                user_id=owner_user.id
            )

    def test_transfer_ownership_archived_workspace_fails(
        self, workspace_service, db_session, archived_workspace, owner_user, member_user
    ):
        """Cannot transfer ownership of archived workspace"""
        member = WorkspaceMember(
            workspace_id=archived_workspace.id,
            user_id=member_user.id,
            role=MemberRole.FULL,
            status=MemberStatus.ACTIVE,
        )
        db_session.add(member)
        db_session.commit()
        
        with pytest.raises(WorkspaceArchivedError):
            workspace_service.transfer_ownership(
                workspace_id=archived_workspace.id,
                new_owner_id=member_user.id,
                user_id=owner_user.id
            )
