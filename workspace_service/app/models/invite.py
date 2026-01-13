from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.member import MemberRole
import uuid
import enum


class InviteStatus(str, enum.Enum):
    """
    Invitation statuses:
    - PENDING: Waiting for invitee response
    - ACCEPTED: Invitee accepted, membership created
    - REJECTED: Invitee explicitly declined
    - EXPIRED: 3 days passed without response
    - CANCELED: Owner canceled the invitation
    """
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELED = "canceled"


class WorkspaceInvite(Base):
    __tablename__ = "workspace_invites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    inviter_user_id = Column(Integer, nullable=False, index=True)
    invitee_user_id = Column(Integer, nullable=False, index=True)  # Required - must be existing user
    invitee_email = Column(String(255), nullable=False)  # Stored for display purposes
    role = Column(
        Enum(MemberRole, native_enum=False, length=50), 
        nullable=False, 
        default=MemberRole.READ
    )  # Role to assign upon acceptance
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(InviteStatus, native_enum=False, length=50), nullable=False, default=InviteStatus.PENDING)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)  # When invitee responded (accept/reject)

    # Relationships
    workspace = relationship("Workspace", back_populates="invites")

    # Indexes for common queries
    # Note: inviter_user_id and invitee_user_id already have index=True on column definition
    __table_args__ = (
        Index("ix_workspace_invites_workspace_id", "workspace_id"),
        Index("ix_workspace_invites_status", "status"),
        # Composite index for workspace+user lookups
        # Note: Uniqueness for pending invites is enforced by application logic
        # (checking _get_pending_invite before creating)
        Index(
            "ix_workspace_invites_workspace_invitee",
            "workspace_id", "invitee_user_id",
        ),
    )

    @property
    def is_pending(self) -> bool:
        """Check if invite is still pending"""
        return self.status == InviteStatus.PENDING

    @property
    def is_expired(self) -> bool:
        """Check if invite has expired (time-based)"""
        from datetime import datetime, timezone as tz
        now = datetime.now(tz.utc)
        expires_at = self.expires_at
        
        # Handle both timezone-aware and naive datetimes (SQLite vs PostgreSQL)
        if expires_at.tzinfo is None:
            # Treat naive datetime as UTC
            expires_at = expires_at.replace(tzinfo=tz.utc)
        
        return expires_at <= now

    @property
    def is_actionable(self) -> bool:
        """Check if invite can be accepted/rejected (pending and not expired)"""
        return self.is_pending and not self.is_expired

    def can_be_reinvited(self) -> bool:
        """Check if user can be re-invited (expired or rejected status)"""
        return self.status in (InviteStatus.EXPIRED, InviteStatus.REJECTED, InviteStatus.CANCELED)

