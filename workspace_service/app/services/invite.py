from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone, timedelta

from app.models.invite import WorkspaceInvite, InviteStatus
from app.models.member import MemberRole, MemberStatus
from app.models.workspace import Workspace
from app.schemas.invite import InviteCreate
from app.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceAccessDeniedError,
    WorkspaceArchivedError,
    InviteNotFoundError,
    InviteExpiredError,
    InviteAlreadyUsedError,
    InvalidInviteTokenError,
    MemberAlreadyExistsError,
)
from app.services.workspace import WorkspaceService
from app.utils.logger import get_logger, log_operation
from app.utils.token import generate_invite_token, hash_token
from app.config import settings

logger = get_logger(__name__)


class InviteService:
    def __init__(self, db: Session, workspace_service: WorkspaceService):
        self.db = db
        self.workspace_service = workspace_service

    def create_invite(
        self, workspace_id: UUID, user_id: int, data: InviteCreate
    ) -> tuple[WorkspaceInvite, str]:
        """
        Create a new invite to a workspace.
        
        Returns:
            Tuple of (invite, plain_token) where plain_token should be sent to the invitee
        """
        # Verify workspace exists and user has permission
        workspace = self.workspace_service.get_workspace(workspace_id, user_id)
        member = self.workspace_service._get_member(workspace_id, user_id)

        if not member.can_invite():
            raise WorkspaceAccessDeniedError("Only admins and owners can send invites")

        if workspace.is_archived:
            raise WorkspaceArchivedError(workspace_id)

        # Check if invitee is already a member
        if data.invitee_user_id:
            existing = self.workspace_service._get_member(workspace_id, data.invitee_user_id)
            if existing and existing.status == MemberStatus.ACTIVE:
                raise MemberAlreadyExistsError(data.invitee_user_id, workspace_id)

        # Generate secure token
        plain_token, token_hash = generate_invite_token()

        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.INVITE_TOKEN_EXPIRE_DAYS)

        invite = WorkspaceInvite(
            workspace_id=workspace_id,
            inviter_user_id=user_id,
            invitee_user_id=data.invitee_user_id,
            invitee_email=data.invitee_email,
            token_hash=token_hash,
            expires_at=expires_at,
            status=InviteStatus.PENDING,
        )

        self.db.add(invite)
        self.db.commit()
        self.db.refresh(invite)

        log_operation(
            logger, "invite_created", user_id,
            f"Workspace: {workspace_id}, Invite: {invite.id}"
        )

        return invite, plain_token

    def get_workspace_invites(self, workspace_id: UUID, user_id: int) -> List[WorkspaceInvite]:
        """Get all pending invites for a workspace"""
        self.workspace_service.get_workspace(workspace_id, user_id)  # Verify access

        return (
            self.db.query(WorkspaceInvite)
            .filter(
                WorkspaceInvite.workspace_id == workspace_id,
                WorkspaceInvite.status == InviteStatus.PENDING,
            )
            .all()
        )

    def revoke_invite(self, workspace_id: UUID, invite_id: UUID, user_id: int) -> None:
        """Revoke an invite"""
        workspace = self.workspace_service.get_workspace(workspace_id, user_id)
        member = self.workspace_service._get_member(workspace_id, user_id)

        if not member.can_invite():
            raise WorkspaceAccessDeniedError("Only admins and owners can revoke invites")

        invite = (
            self.db.query(WorkspaceInvite)
            .filter(
                WorkspaceInvite.id == invite_id,
                WorkspaceInvite.workspace_id == workspace_id,
            )
            .first()
        )

        if not invite:
            raise InviteNotFoundError(invite_id)

        if invite.status != InviteStatus.PENDING:
            raise InviteAlreadyUsedError()

        invite.status = InviteStatus.REVOKED
        self.db.commit()

        log_operation(
            logger, "invite_revoked", user_id,
            f"Workspace: {workspace_id}, Invite: {invite_id}"
        )

    def accept_invite(self, token: str, user_id: int) -> WorkspaceInvite:
        """Accept an invite using the token"""
        token_hash = hash_token(token)

        invite = (
            self.db.query(WorkspaceInvite)
            .filter(WorkspaceInvite.token_hash == token_hash)
            .first()
        )

        if not invite:
            raise InvalidInviteTokenError()

        if invite.status != InviteStatus.PENDING:
            raise InviteAlreadyUsedError()

        if invite.expires_at < datetime.now(timezone.utc):
            invite.status = InviteStatus.EXPIRED
            self.db.commit()
            raise InviteExpiredError()

        # If invite was for a specific user, verify it matches
        if invite.invitee_user_id and invite.invitee_user_id != user_id:
            raise WorkspaceAccessDeniedError("This invite was sent to a different user")

        # Check workspace still exists and is not archived
        workspace = self.db.query(Workspace).filter(Workspace.id == invite.workspace_id).first()
        if not workspace:
            raise WorkspaceNotFoundError(invite.workspace_id)

        if workspace.is_archived:
            raise WorkspaceArchivedError(invite.workspace_id)

        # Add user as member (default role is MEMBER unless specified in invite logic)
        self.workspace_service.add_member(invite.workspace_id, user_id, MemberRole.MEMBER)

        # Mark invite as accepted
        invite.status = InviteStatus.ACCEPTED
        invite.accepted_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(invite)

        log_operation(
            logger, "invite_accepted", user_id,
            f"Workspace: {invite.workspace_id}, Invite: {invite.id}"
        )

        return invite

    def decline_invite(self, token: str, user_id: int) -> None:
        """Decline an invite"""
        token_hash = hash_token(token)

        invite = (
            self.db.query(WorkspaceInvite)
            .filter(WorkspaceInvite.token_hash == token_hash)
            .first()
        )

        if not invite:
            raise InvalidInviteTokenError()

        if invite.status != InviteStatus.PENDING:
            raise InviteAlreadyUsedError()

        # If invite was for a specific user, verify it matches
        if invite.invitee_user_id and invite.invitee_user_id != user_id:
            raise WorkspaceAccessDeniedError("This invite was sent to a different user")

        invite.status = InviteStatus.REVOKED
        self.db.commit()

        log_operation(
            logger, "invite_declined", user_id,
            f"Workspace: {invite.workspace_id}, Invite: {invite.id}"
        )

    def get_invite_by_token(self, token: str) -> Optional[WorkspaceInvite]:
        """Get invite details by token (for preview before accepting)"""
        token_hash = hash_token(token)

        invite = (
            self.db.query(WorkspaceInvite)
            .filter(WorkspaceInvite.token_hash == token_hash)
            .first()
        )

        if not invite:
            return None

        # Check if expired
        if invite.status == InviteStatus.PENDING and invite.expires_at < datetime.now(timezone.utc):
            invite.status = InviteStatus.EXPIRED
            self.db.commit()

        return invite

    def cleanup_expired_invites(self) -> int:
        """Mark expired invites as expired (can be run periodically)"""
        now = datetime.now(timezone.utc)
        result = (
            self.db.query(WorkspaceInvite)
            .filter(
                WorkspaceInvite.status == InviteStatus.PENDING,
                WorkspaceInvite.expires_at < now,
            )
            .update({"status": InviteStatus.EXPIRED})
        )
        self.db.commit()
        return result

