from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
import enum


class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class WorkspaceInvite(Base):
    __tablename__ = "workspace_invites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    inviter_user_id = Column(Integer, nullable=False)
    invitee_user_id = Column(Integer, nullable=True)  # For direct user invites
    invitee_email = Column(String(255), nullable=True)  # For email invites
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(InviteStatus), nullable=False, default=InviteStatus.PENDING)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="invites")

    # Indexes
    __table_args__ = (
        Index("ix_workspace_invites_token_hash", "token_hash"),
        Index("ix_workspace_invites_workspace_id", "workspace_id"),
        Index("ix_workspace_invites_invitee_email", "invitee_email"),
    )

    @property
    def is_pending(self) -> bool:
        """Check if invite is still pending"""
        return self.status == InviteStatus.PENDING

    @property
    def is_valid(self) -> bool:
        """Check if invite is still valid (pending and not expired)"""
        from datetime import datetime, timezone
        return self.is_pending and self.expires_at > datetime.now(timezone.utc)

