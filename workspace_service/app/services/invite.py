"""
Invite Service - Handles workspace invitation logic.

Business Rules:
1. Only workspace owner can create/cancel invites
2. Invitee must be an existing user (looked up by email)
3. Only one PENDING invite per (workspace_id, invitee_user_id)
4. If PENDING invite exists → return existing (don't create new)
5. If status is EXPIRED/REJECTED/CANCELED → allow creating new invite
6. If invitee is already a member → error
7. Invites expire after 3 days
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.models.invite import WorkspaceInvite, InviteStatus
from app.models.member import MemberRole, MemberStatus, WorkspaceMember
from app.models.workspace import Workspace
from app.schemas.invite import InviteCreate, MyInviteResponse
from app.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceAccessDeniedError,
    WorkspaceArchivedError,
    InviteNotFoundError,
    InviteExpiredError,
    InviteAlreadyUsedError,
    InviteNotActionableError,
    InviteeNotFoundError,
    SelfInviteNotAllowedError,
    MemberAlreadyExistsError,
)
from app.clients.user import UserClient, UserInfo
from app.utils.logger import get_logger, log_operation
from app.config import settings

logger = get_logger(__name__)


class InviteService:
    def __init__(self, db: Session):
        self.db = db
        self.user_client = UserClient()

    # ==================== Owner Operations ====================

    def create_invite(
        self, workspace_id: UUID, owner_user_id: int, data: InviteCreate
    ) -> tuple[WorkspaceInvite, bool]:
        """
        Create a new invite to a workspace.
        
        Args:
            workspace_id: Workspace to invite to
            owner_user_id: ID of the user creating the invite (must be owner)
            data: Invite creation data (email, role)
        
        Returns:
            Tuple of (invite, is_new) where is_new is True if created, False if existing returned
            
        Raises:
            WorkspaceNotFoundError: Workspace doesn't exist
            WorkspaceAccessDeniedError: User is not the owner
            WorkspaceArchivedError: Workspace is archived
            InviteeNotFoundError: No user found with the given email
            SelfInviteNotAllowedError: Owner trying to invite themselves
            MemberAlreadyExistsError: Invitee is already a member
        """
        # 1. Verify workspace exists
        workspace = self._get_workspace(workspace_id)
        if not workspace:
            raise WorkspaceNotFoundError(workspace_id)
        
        # 2. Verify user is owner
        if not self._is_owner(workspace_id, owner_user_id):
            raise WorkspaceAccessDeniedError("Only the workspace owner can send invites")

        # 3. Check workspace is not archived
        if workspace.is_archived:
            raise WorkspaceArchivedError(workspace_id)

        # 4. Look up invitee by email
        invitee = self.user_client.get_user_by_email(data.email.lower().strip())
        if not invitee:
            raise InviteeNotFoundError(data.email)
        
        # 5. Cannot invite yourself
        if invitee.id == owner_user_id:
            raise SelfInviteNotAllowedError()
        
        # 6. Check if invitee is already a member
        existing_member = self._get_member(workspace_id, invitee.id)
        if existing_member and existing_member.status == MemberStatus.ACTIVE:
            raise MemberAlreadyExistsError(invitee.id, workspace_id)

        # 7. Check for existing PENDING invite
        existing_invite = self._get_pending_invite(workspace_id, invitee.id)
        if existing_invite:
            log_operation(
                logger, "invite_exists", owner_user_id,
                f"Returning existing invite {existing_invite.id} for user {invitee.id}"
            )
            return existing_invite, False
        
        # 8. Convert role string to MemberRole enum
        role = MemberRole.FULL if data.role == "full" else MemberRole.READ
        
        # 9. Create new invite
        # Use naive datetime for SQLite compatibility (all times are UTC)
        expires_at = datetime.utcnow() + timedelta(days=settings.INVITE_EXPIRE_DAYS)

        invite = WorkspaceInvite(
            workspace_id=workspace_id,
            inviter_user_id=owner_user_id,
            invitee_user_id=invitee.id,
            invitee_email=invitee.email,
            role=role,
            expires_at=expires_at,
            status=InviteStatus.PENDING,
        )

        self.db.add(invite)
        self.db.commit()
        self.db.refresh(invite)

        log_operation(
            logger, "invite_created", owner_user_id,
            f"Workspace: {workspace_id}, Invitee: {invitee.id}, Role: {role}"
        )

        return invite, True

    def get_workspace_invites(
        self, workspace_id: UUID, user_id: int, status_filter: Optional[InviteStatus] = None
    ) -> List[WorkspaceInvite]:
        """
        Get invites for a workspace (owner only).
        
        Args:
            workspace_id: Workspace ID
            user_id: Requesting user (must be owner)
            status_filter: Optional filter by status (defaults to PENDING)
        """
        # Verify ownership
        if not self._is_owner(workspace_id, user_id):
            raise WorkspaceAccessDeniedError("Only the workspace owner can view invites")
        
        query = self.db.query(WorkspaceInvite).filter(
            WorkspaceInvite.workspace_id == workspace_id
        )
        
        if status_filter:
            query = query.filter(WorkspaceInvite.status == status_filter)
        else:
            # Default: show pending invites
            query = query.filter(WorkspaceInvite.status == InviteStatus.PENDING)
        
        return query.order_by(WorkspaceInvite.created_at.desc()).all()

    def cancel_invite(self, workspace_id: UUID, invite_id: UUID, user_id: int) -> None:
        """
        Cancel a pending invite (owner only).
        
        Args:
            workspace_id: Workspace ID
            invite_id: Invite to cancel
            user_id: User canceling (must be owner)
        """
        # Verify ownership
        if not self._is_owner(workspace_id, user_id):
            raise WorkspaceAccessDeniedError("Only the workspace owner can cancel invites")

        invite = self.db.query(WorkspaceInvite).filter(
                WorkspaceInvite.id == invite_id,
                WorkspaceInvite.workspace_id == workspace_id,
        ).first()

        if not invite:
            raise InviteNotFoundError(invite_id)

        if invite.status != InviteStatus.PENDING:
            raise InviteAlreadyUsedError()

        invite.status = InviteStatus.CANCELED
        invite.responded_at = datetime.utcnow()
        self.db.commit()

        log_operation(
            logger, "invite_canceled", user_id,
            f"Workspace: {workspace_id}, Invite: {invite_id}"
        )

    # ==================== Invitee Operations ====================

    def get_my_invites(
        self, user_id: int, include_all: bool = False
    ) -> List[MyInviteResponse]:
        """
        Get all invites for the current user (invitee view).
        
        Args:
            user_id: The invitee user ID
            include_all: If True, include non-pending invites
            
        Returns:
            List of MyInviteResponse with rich workspace/inviter info
        """
        query = self.db.query(WorkspaceInvite).filter(
            WorkspaceInvite.invitee_user_id == user_id
        )
        
        if not include_all:
            # Only show pending invites by default
            query = query.filter(WorkspaceInvite.status == InviteStatus.PENDING)
        
        invites = query.order_by(WorkspaceInvite.created_at.desc()).all()
        
        # Fetch workspace and inviter info for each invite
        result = []
        for invite in invites:
            workspace = self._get_workspace(invite.workspace_id)
            inviter = self.user_client.get_user(invite.inviter_user_id)
            
            if workspace and inviter:
                result.append(MyInviteResponse(
                    id=invite.id,
                    workspace_id=invite.workspace_id,
                    workspace_name=workspace.name,
                    inviter_user_id=invite.inviter_user_id,
                    inviter_email=inviter.email,
                    inviter_username=inviter.username,
                    role=invite.role,
                    status=invite.status,
                    expires_at=invite.expires_at,
                    created_at=invite.created_at,
                ))
        
        return result

    def accept_invite(self, invite_id: UUID, user_id: int) -> WorkspaceInvite:
        """
        Accept an invite (invitee only, pending and not expired).
        
        Creates membership with the specified role.
        
        Args:
            invite_id: Invite to accept
            user_id: User accepting (must be the invitee)
            
        Returns:
            Updated invite
            
        Raises:
            InviteNotFoundError: Invite doesn't exist
            WorkspaceAccessDeniedError: User is not the invitee
            InviteNotActionableError: Invite is not pending or has expired
        """
        invite = self._get_invite(invite_id)
        if not invite:
            raise InviteNotFoundError(invite_id)

        # Verify user is the invitee
        if invite.invitee_user_id != user_id:
            raise WorkspaceAccessDeniedError("This invite was sent to a different user")

        # Check if actionable
        if not invite.is_actionable:
            if invite.is_expired:
                # Mark as expired
                invite.status = InviteStatus.EXPIRED
                self.db.commit()
                raise InviteExpiredError()
            raise InviteNotActionableError(
                f"Cannot accept invite with status: {invite.status.value}"
            )

        # Check workspace still exists and is not archived
        workspace = self._get_workspace(invite.workspace_id)
        if not workspace:
            raise WorkspaceNotFoundError(invite.workspace_id)
        if workspace.is_archived:
            raise WorkspaceArchivedError(invite.workspace_id)

        # Create or reactivate membership
        self._add_member(invite.workspace_id, user_id, invite.role)

        # Mark invite as accepted
        now = datetime.utcnow()
        invite.status = InviteStatus.ACCEPTED
        invite.accepted_at = now
        invite.responded_at = now
        self.db.commit()
        self.db.refresh(invite)

        log_operation(
            logger, "invite_accepted", user_id,
            f"Workspace: {invite.workspace_id}, Role: {invite.role}"
        )

        return invite

    def reject_invite(self, invite_id: UUID, user_id: int) -> None:
        """
        Reject an invite (invitee only, pending and not expired).
        
        Args:
            invite_id: Invite to reject
            user_id: User rejecting (must be the invitee)
        """
        invite = self._get_invite(invite_id)
        if not invite:
            raise InviteNotFoundError(invite_id)
        
        # Verify user is the invitee
        if invite.invitee_user_id != user_id:
            raise WorkspaceAccessDeniedError("This invite was sent to a different user")

        # Check if actionable
        if not invite.is_actionable:
            if invite.is_expired:
                invite.status = InviteStatus.EXPIRED
                self.db.commit()
                raise InviteExpiredError()
            raise InviteNotActionableError(
                f"Cannot reject invite with status: {invite.status.value}"
            )
        
        # Mark as rejected
        invite.status = InviteStatus.REJECTED
        invite.responded_at = datetime.utcnow()
        self.db.commit()

        log_operation(
            logger, "invite_rejected", user_id,
            f"Workspace: {invite.workspace_id}, Invite: {invite_id}"
        )

    # ==================== Maintenance Operations ====================

    def expire_old_invites(self) -> int:
        """
        Mark expired invites as EXPIRED (can be run periodically).
        
        Returns:
            Number of invites marked as expired
        """
        # Use naive datetime for SQLite compatibility (which doesn't preserve timezone info)
        # All datetimes are treated as UTC in this application
        now = datetime.utcnow()
        result = (
            self.db.query(WorkspaceInvite)
            .filter(
                WorkspaceInvite.status == InviteStatus.PENDING,
                WorkspaceInvite.expires_at < now,
            )
            .update({"status": InviteStatus.EXPIRED})
        )
        self.db.commit()
        
        if result > 0:
            logger.info(f"Marked {result} invites as expired")
        
        return result

    # ==================== Internal Helpers ====================

    def _get_workspace(self, workspace_id: UUID) -> Optional[Workspace]:
        """Get workspace by ID"""
        return self.db.query(Workspace).filter(Workspace.id == workspace_id).first()

    def _get_invite(self, invite_id: UUID) -> Optional[WorkspaceInvite]:
        """Get invite by ID"""
        return self.db.query(WorkspaceInvite).filter(
            WorkspaceInvite.id == invite_id
        ).first()

    def _get_member(self, workspace_id: UUID, user_id: int) -> Optional[WorkspaceMember]:
        """Get member record (including inactive)"""
        return self.db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        ).first()

    def _is_owner(self, workspace_id: UUID, user_id: int) -> bool:
        """Check if user is the workspace owner"""
        member = self._get_member(workspace_id, user_id)
        return member is not None and member.role == MemberRole.OWNER and member.is_active

    def _get_pending_invite(
        self, workspace_id: UUID, invitee_user_id: int
    ) -> Optional[WorkspaceInvite]:
        """Get existing pending invite for workspace+user"""
        return self.db.query(WorkspaceInvite).filter(
            WorkspaceInvite.workspace_id == workspace_id,
            WorkspaceInvite.invitee_user_id == invitee_user_id,
            WorkspaceInvite.status == InviteStatus.PENDING,
        ).first()

    def _add_member(
        self, workspace_id: UUID, user_id: int, role: MemberRole
    ) -> WorkspaceMember:
        """Add or reactivate a member"""
        existing = self._get_member(workspace_id, user_id)
        
        if existing:
            # Reactivate existing member with new role
            existing.status = MemberStatus.ACTIVE
            existing.role = role
            existing.joined_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new member
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
            status=MemberStatus.ACTIVE,
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        
        return member
