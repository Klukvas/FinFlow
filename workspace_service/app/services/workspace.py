from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from app.models.workspace import Workspace, WorkspaceType
from app.models.member import WorkspaceMember, MemberRole, MemberStatus
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse
from app.schemas.member import MemberRoleUpdate, MemberResponse
from app.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceValidationError,
    WorkspaceAccessDeniedError,
    WorkspaceArchivedError,
    WorkspaceLimitExceededError,
    MemberNotFoundError,
    MemberAlreadyExistsError,
    InvalidRoleChangeError,
    OwnerCannotLeaveError,
    PersonalWorkspaceProtectedError,
)
from app.clients.subscription import SubscriptionClient
from app.clients.user import UserClient
from app.utils.logger import get_logger, log_operation

logger = get_logger(__name__)


# Role hierarchy for permission checks (simplified)
# owner > full > read
ROLE_HIERARCHY = {
    MemberRole.OWNER: 3,
    MemberRole.FULL: 2,
    MemberRole.READ: 1,
}


class WorkspaceService:
    def __init__(self, db: Session):
        self.db = db
        self.subscription_client = SubscriptionClient()
        self.user_client = UserClient()

    # ==================== Workspace Operations ====================

    def _get_user_workspace_count(self, user_id: int) -> int:
        """Get count of workspaces owned by user (excluding archived)"""
        return (
            self.db.query(Workspace)
            .filter(
                Workspace.owner_user_id == user_id,
                Workspace.archived_at.is_(None),
            )
            .count()
        )

    def create_workspace(self, user_id: int, data: WorkspaceCreate) -> Workspace:
        """Create a new workspace with the user as owner"""
        try:
            # Check workspace limit
            current_count = self._get_user_workspace_count(user_id)
            if not self.subscription_client.check_workspace_limit(user_id, current_count):
                limit = self.subscription_client.get_workspace_limit(user_id)
                raise WorkspaceLimitExceededError(current_count, limit or 1)

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

        except WorkspaceLimitExceededError:
            raise
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

    def get_members(self, workspace_id: UUID, user_id: int) -> List[MemberResponse]:
        """
        Get all active members of a workspace with user details.
        
        Any workspace member can view the member list.
        """
        self.get_workspace(workspace_id, user_id)  # Verify access
        
        members = (
            self.db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.status == MemberStatus.ACTIVE,
            )
            .all()
        )
        
        # Fetch user info for all members
        user_ids = [m.user_id for m in members]
        users_info = self.user_client.get_users_batch(user_ids)
        
        result = []
        for member in members:
            user_info = users_info.get(member.user_id)
            result.append(MemberResponse(
                id=member.id,
                workspace_id=member.workspace_id,
                user_id=member.user_id,
                role=member.role,
                status=member.status,
                joined_at=member.joined_at,
                created_at=member.created_at,
                updated_at=member.updated_at,
                email=user_info.email if user_info else None,
            ))
        
        return result

    def update_member_role(
        self, workspace_id: UUID, target_user_id: int, user_id: int, data: MemberRoleUpdate
    ) -> WorkspaceMember:
        """
        Update a member's role (owner only).
        
        Can change between READ and FULL roles.
        Cannot change owner role or promote to owner.
        """
        workspace = self.get_workspace(workspace_id, user_id)
        actor_member = self._get_member(workspace_id, user_id)
        target_member = self._get_member(workspace_id, target_user_id)

        if not target_member or not target_member.is_active:
            raise MemberNotFoundError(target_user_id, workspace_id)

        if workspace.is_archived:
            raise WorkspaceArchivedError(workspace_id)

        # Only owner can manage roles
        if actor_member.role != MemberRole.OWNER:
            raise WorkspaceAccessDeniedError("Only the workspace owner can change member roles")

        # Cannot change owner role this way
        if target_member.role == MemberRole.OWNER:
            raise InvalidRoleChangeError("Cannot change owner role. Use ownership transfer instead.")

        # Convert string role to MemberRole enum
        new_role = MemberRole.FULL if data.role == "full" else MemberRole.READ

        target_member.role = new_role
        self.db.commit()
        self.db.refresh(target_member)

        log_operation(
            logger, "member_role_updated", user_id,
            f"Workspace: {workspace_id}, User: {target_user_id}, Role: {new_role}"
        )
        return target_member

    def remove_member(self, workspace_id: UUID, target_user_id: int, user_id: int) -> None:
        """
        Remove a member from a workspace (owner only).
        
        Removed members can be re-invited.
        """
        workspace = self.get_workspace(workspace_id, user_id)
        actor_member = self._get_member(workspace_id, user_id)
        target_member = self._get_member(workspace_id, target_user_id)

        if not target_member or not target_member.is_active:
            raise MemberNotFoundError(target_user_id, workspace_id)

        if workspace.is_archived:
            raise WorkspaceArchivedError(workspace_id)

        # Cannot remove the owner
        if target_member.role == MemberRole.OWNER:
            raise InvalidRoleChangeError("Cannot remove the workspace owner")

        # Only owner can remove members
        if actor_member.role != MemberRole.OWNER:
            raise WorkspaceAccessDeniedError("Only the workspace owner can remove members")

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

        # Transfer ownership - previous owner becomes FULL member
        current_owner.role = MemberRole.FULL
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
        self, workspace_id: UUID, new_user_id: int, role: MemberRole = MemberRole.READ
    ) -> WorkspaceMember:
        """
        Add a new member to a workspace (internal use, e.g., after invite acceptance).
        
        If member was previously removed/left, reactivates them with the new role.
        """
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

