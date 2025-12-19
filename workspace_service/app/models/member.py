from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class MemberRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class MemberStatus(str, enum.Enum):
    ACTIVE = "active"
    LEFT = "left"
    REMOVED = "removed"


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    role = Column(Enum(MemberRole), nullable=False, default=MemberRole.MEMBER)
    status = Column(Enum(MemberStatus), nullable=False, default=MemberStatus.ACTIVE)
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="members")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
        Index("ix_workspace_members_workspace_id", "workspace_id"),
    )

    @property
    def is_active(self) -> bool:
        """Check if member is active"""
        return self.status == MemberStatus.ACTIVE

    def can_manage_members(self) -> bool:
        """Check if member can manage other members"""
        return self.role in (MemberRole.OWNER, MemberRole.ADMIN) and self.is_active

    def can_invite(self) -> bool:
        """Check if member can send invites"""
        return self.role in (MemberRole.OWNER, MemberRole.ADMIN) and self.is_active

    def can_write(self) -> bool:
        """Check if member has write access"""
        return self.role in (MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER) and self.is_active

    def can_read(self) -> bool:
        """Check if member has read access"""
        return self.is_active

