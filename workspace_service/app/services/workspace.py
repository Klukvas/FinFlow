from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from app.models.workspace import Workspace, WorkspaceType
from app.models.member import WorkspaceMember, MemberRole, MemberStatus
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
from app.schemas.member import MemberRoleUpdate
from app.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceValidationError,
    WorkspaceAccessDeniedError,
    WorkspaceArchivedError,
    MemberNotFoundError,
    MemberAlreadyExistsError,
    InvalidRoleChangeError,
    OwnerCannotLeaveError,
    PersonalWorkspaceProtectedError,
)
from app.utils.logger import get_logger, log_operation

logger = get_logger(__name__)


# Role hierarchy for permission checks
ROLE_HIERARCHY = {
    MemberRole.OWNER: 4,
    MemberRole.ADMIN: 3,
    MemberRole.MEMBER: 2,
    MemberRole.VIEWER: 1,
}


class WorkspaceService:
    def __init__(self, db: Session):
        self.db = db

    # ==================== Workspace Operations ====================

    def create_workspace(self, user_id: int, data: WorkspaceCreate) -> Workspace:
        """Create a new workspace with the user as owner"""
        try:
            workspace = Workspace(
                name=data.name.strip(),
                type=data.type,
                owner_user_id=user_id,
            )
            self.db.add(workspace)
            self.db.flush()

            # Add creator as owner member
            member = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=user_id,
                role=MemberRole.OWNER,
                status=MemberStatus.ACTIVE,
            )
            self.db.add(member)
            self.db.commit()
            self.db.refresh(workspace)

            log_operation(logger, "workspace_created", user_id, f"Workspace: {workspace.id}")
            return workspace

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating workspace: {e}")
            raise WorkspaceValidationError(f"Failed to create workspace: {str(e)}")

    def create_personal_workspace(self, user_id: int) -> Workspace:
        """Create a personal workspace for a new user (called during registration)"""
        try:
            workspace = Workspace(
                name="Personal",
                type=WorkspaceType.PERSONAL,
                owner_user_id=user_id,
            )
            self.db.add(workspace)
            self.db.flush()

            member = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=user_id,
                role=MemberRole.OWNER,
                status=MemberStatus.ACTIVE,
            )
            self.db.add(member)
            self.db.commit()
            self.db.refresh(workspace)

            log_operation(logger, "personal_workspace_created", user_id, f"Workspace: {workspace.id}")
            return workspace

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating personal workspace: {e}")
            raise WorkspaceValidationError(f"Failed to create personal workspace: {str(e)}")

    def get_workspace(self, workspace_id: UUID, user_id: int) -> Workspace:
        """Get a workspace by ID, verifying user access"""
        workspace = self.db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise WorkspaceNotFoundError(workspace_id)

        # Verify user is a member
        member = self._get_member(workspace_id, user_id)
        if not member or not member.is_active:
            raise WorkspaceAccessDeniedError()

        return workspace

    def get_user_workspaces(self, user_id: int, include_archived: bool = False) -> List[Workspace]:
        """Get all workspaces for a user"""
        query = (
            self.db.query(Workspace)
            .join(WorkspaceMember)
            .filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.status == MemberStatus.ACTIVE,
            )
        )

        if not include_archived:
            query = query.filter(Workspace.archived_at.is_(None))

        return query.all()

    def get_user_default_workspace(self, user_id: int) -> Optional[Workspace]:
        """Get user's default (personal) workspace"""
        return (
            self.db.query(Workspace)
            .join(WorkspaceMember)
            .filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.status == MemberStatus.ACTIVE,
                Workspace.type == WorkspaceType.PERSONAL,
                Workspace.archived_at.is_(None),
            )
            .first()
        )

    def update_workspace(self, workspace_id: UUID, user_id: int, data: WorkspaceUpdate) -> Workspace:
        """Update workspace details"""
        workspace = self.get_workspace(workspace_id, user_id)
        member = self._get_member(workspace_id, user_id)

        if not member.can_manage_members():
            raise WorkspaceAccessDeniedError("Only admins and owners can update workspace settings")

        if workspace.is_archived:
            raise WorkspaceArchivedError(workspace_id)

        # Protect personal workspace - only allow name change, not type change
        if workspace.type == WorkspaceType.PERSONAL:
            # Personal workspace name can be changed, but it's recommended to keep it as "Personal"
            if data.name is not None:
                workspace.name = data.name.strip()
        else:
            # Regular workspace can have name changed
            if data.name is not None:
                workspace.name = data.name.strip()

        self.db.commit()
        self.db.refresh(workspace)

        log_operation(logger, "workspace_updated", user_id, f"Workspace: {workspace_id}")
        return workspace

    def archive_workspace(self, workspace_id: UUID, user_id: int) -> Workspace:
        """Archive a workspace"""
        workspace = self.get_workspace(workspace_id, user_id)
        member = self._get_member(workspace_id, user_id)

        # Protect personal workspace from being archived
        if workspace.type == WorkspaceType.PERSONAL:
            raise PersonalWorkspaceProtectedError("Personal workspace cannot be archived")

        if member.role != MemberRole.OWNER:
            raise WorkspaceAccessDeniedError("Only the owner can archive a workspace")

        if workspace.is_archived:
            raise WorkspaceArchivedError(workspace_id)

        workspace.archived_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(workspace)

        log_operation(logger, "workspace_archived", user_id, f"Workspace: {workspace_id}")
        return workspace

    def unarchive_workspace(self, workspace_id: UUID, user_id: int) -> Workspace:
        """Unarchive a workspace"""
        workspace = self.db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise WorkspaceNotFoundError(workspace_id)

        member = self._get_member(workspace_id, user_id)
        if not member or member.role != MemberRole.OWNER:
            raise WorkspaceAccessDeniedError("Only the owner can unarchive a workspace")

        if not workspace.is_archived:
            raise WorkspaceValidationError("Workspace is not archived")

        workspace.archived_at = None
        self.db.commit()
        self.db.refresh(workspace)

        log_operation(logger, "workspace_unarchived", user_id, f"Workspace: {workspace_id}")
        return workspace

    # ==================== Member Operations ====================

    def get_members(self, workspace_id: UUID, user_id: int) -> List[WorkspaceMember]:
        """Get all members of a workspace"""
        self.get_workspace(workspace_id, user_id)  # Verify access
        return (
            self.db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.status == MemberStatus.ACTIVE,
            )
            .all()
        )

    def update_member_role(
        self, workspace_id: UUID, target_user_id: int, user_id: int, data: MemberRoleUpdate
    ) -> WorkspaceMember:
        """Update a member's role"""
        workspace = self.get_workspace(workspace_id, user_id)
        actor_member = self._get_member(workspace_id, user_id)
        target_member = self._get_member(workspace_id, target_user_id)

        if not target_member:
            raise MemberNotFoundError(target_user_id, workspace_id)

        if workspace.is_archived:
            raise WorkspaceArchivedError(workspace_id)

        if not actor_member.can_manage_members():
            raise WorkspaceAccessDeniedError("Only admins and owners can change member roles")

        # Cannot change owner role this way
        if target_member.role == MemberRole.OWNER:
            raise InvalidRoleChangeError("Cannot change owner role. Use ownership transfer instead.")

        # Cannot promote to owner this way
        if data.role == MemberRole.OWNER:
            raise InvalidRoleChangeError("Cannot promote to owner. Use ownership transfer instead.")

        # Admin cannot promote to admin (only owner can)
        if actor_member.role == MemberRole.ADMIN and data.role == MemberRole.ADMIN:
            raise InvalidRoleChangeError("Only the owner can promote members to admin")

        target_member.role = data.role
        self.db.commit()
        self.db.refresh(target_member)

        log_operation(
            logger, "member_role_updated", user_id,
            f"Workspace: {workspace_id}, User: {target_user_id}, Role: {data.role}"
        )
        return target_member

    def remove_member(self, workspace_id: UUID, target_user_id: int, user_id: int) -> None:
        """Remove a member from a workspace"""
        workspace = self.get_workspace(workspace_id, user_id)
        actor_member = self._get_member(workspace_id, user_id)
        target_member = self._get_member(workspace_id, target_user_id)

        if not target_member:
            raise MemberNotFoundError(target_user_id, workspace_id)

        if workspace.is_archived:
            raise WorkspaceArchivedError(workspace_id)

        # Cannot remove the owner
        if target_member.role == MemberRole.OWNER:
            raise InvalidRoleChangeError("Cannot remove the workspace owner")

        # Only owner and admin can remove members
        if not actor_member.can_manage_members():
            raise WorkspaceAccessDeniedError("Only admins and owners can remove members")

        # Admin cannot remove another admin
        if actor_member.role == MemberRole.ADMIN and target_member.role == MemberRole.ADMIN:
            raise WorkspaceAccessDeniedError("Admin cannot remove another admin")

        target_member.status = MemberStatus.REMOVED
        self.db.commit()

        log_operation(
            logger, "member_removed", user_id,
            f"Workspace: {workspace_id}, Removed user: {target_user_id}"
        )

    def leave_workspace(self, workspace_id: UUID, user_id: int) -> None:
        """Leave a workspace"""
        workspace = self.get_workspace(workspace_id, user_id)
        member = self._get_member(workspace_id, user_id)

        # Protect personal workspace - owner cannot leave
        if workspace.type == WorkspaceType.PERSONAL and member.role == MemberRole.OWNER:
            raise PersonalWorkspaceProtectedError("Cannot leave personal workspace")

        if workspace.is_archived:
            raise WorkspaceArchivedError(workspace_id)

        if member.role == MemberRole.OWNER:
            raise OwnerCannotLeaveError()

        member.status = MemberStatus.LEFT
        self.db.commit()

        log_operation(logger, "member_left", user_id, f"Workspace: {workspace_id}")

    def transfer_ownership(self, workspace_id: UUID, new_owner_id: int, user_id: int) -> Workspace:
        """Transfer workspace ownership to another member"""
        workspace = self.get_workspace(workspace_id, user_id)
        current_owner = self._get_member(workspace_id, user_id)
        new_owner = self._get_member(workspace_id, new_owner_id)

        # Protect personal workspace - ownership cannot be transferred
        if workspace.type == WorkspaceType.PERSONAL:
            raise PersonalWorkspaceProtectedError("Personal workspace ownership cannot be transferred")

        if not new_owner:
            raise MemberNotFoundError(new_owner_id, workspace_id)

        if workspace.is_archived:
            raise WorkspaceArchivedError(workspace_id)

        if current_owner.role != MemberRole.OWNER:
            raise WorkspaceAccessDeniedError("Only the owner can transfer ownership")

        if not new_owner.is_active:
            raise WorkspaceValidationError("Cannot transfer ownership to inactive member")

        # Transfer ownership
        current_owner.role = MemberRole.ADMIN
        new_owner.role = MemberRole.OWNER
        workspace.owner_user_id = new_owner_id

        self.db.commit()
        self.db.refresh(workspace)

        log_operation(
            logger, "ownership_transferred", user_id,
            f"Workspace: {workspace_id}, New owner: {new_owner_id}"
        )
        return workspace

    def add_member(
        self, workspace_id: UUID, new_user_id: int, role: MemberRole = MemberRole.MEMBER
    ) -> WorkspaceMember:
        """Add a new member to a workspace (internal use, e.g., after invite acceptance)"""
        existing = self._get_member(workspace_id, new_user_id)
        if existing and existing.is_active:
            raise MemberAlreadyExistsError(new_user_id, workspace_id)

        if existing:
            # Reactivate existing member
            existing.status = MemberStatus.ACTIVE
            existing.role = role
            existing.joined_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=new_user_id,
            role=role,
            status=MemberStatus.ACTIVE,
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)

        log_operation(logger, "member_added", new_user_id, f"Workspace: {workspace_id}, Role: {role}")
        return member

    # ==================== Authorization ====================

    def authorize(self, workspace_id: UUID, user_id: int, required_role: MemberRole) -> bool:
        """Check if user has the required role in workspace"""
        member = self._get_member(workspace_id, user_id)
        if not member or not member.is_active:
            return False

        user_level = ROLE_HIERARCHY.get(member.role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 0)

        return user_level >= required_level

    def get_user_role(self, workspace_id: UUID, user_id: int) -> Optional[MemberRole]:
        """Get user's role in a workspace"""
        member = self._get_member(workspace_id, user_id)
        if member and member.is_active:
            return member.role
        return None

    def get_member_count(self, workspace_id: UUID) -> int:
        """Get the number of active members in a workspace"""
        return (
            self.db.query(func.count(WorkspaceMember.id))
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.status == MemberStatus.ACTIVE,
            )
            .scalar()
        )

    # ==================== Internal Helpers ====================

    def _get_member(self, workspace_id: UUID, user_id: int) -> Optional[WorkspaceMember]:
        """Get a member record (including inactive)"""
        return (
            self.db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
            .first()
        )

    def get_workspace_response(self, workspace: Workspace, user_id: int) -> WorkspaceResponse:
        """Convert workspace model to response with additional computed fields"""
        member = self._get_member(workspace.id, user_id)
        return WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            type=workspace.type,
            owner_user_id=workspace.owner_user_id,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at,
            archived_at=workspace.archived_at,
            is_archived=workspace.is_archived,
            member_count=self.get_member_count(workspace.id),
            current_user_role=member.role.value if member else None,
        )

