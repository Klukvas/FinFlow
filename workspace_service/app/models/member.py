from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class MemberRole(str, enum.Enum):
    """
    Workspace member roles:
    - OWNER: Full control + member management (invite/remove/change roles)
    - FULL: Full data access (view + create/update/delete workspace data)
    - READ: Read-only access (view workspace data)
    """
    OWNER = "owner"
    FULL = "full"
    READ = "read"


class MemberStatus(str, enum.Enum):
    ACTIVE = "active"
    LEFT = "left"
    REMOVED = "removed"


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    role = Column(Enum(MemberRole, native_enum=False, length=50), nullable=False, default=MemberRole.READ)
    status = Column(Enum(MemberStatus, native_enum=False, length=50), nullable=False, default=MemberStatus.ACTIVE)
    
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

    @property
    def is_owner(self) -> bool:
        """Check if member is the workspace owner"""
        return self.role == MemberRole.OWNER and self.is_active

    def can_manage_members(self) -> bool:
        """Check if member can manage other members (owner only)"""
        return self.role == MemberRole.OWNER and self.is_active

    def can_invite(self) -> bool:
        """Check if member can send invites (owner only)"""
        return self.role == MemberRole.OWNER and self.is_active

    def can_write(self) -> bool:
        """Check if member has write access (owner or full)"""
        return self.role in (MemberRole.OWNER, MemberRole.FULL) and self.is_active

    def can_read(self) -> bool:
        """Check if member has read access (any active member)"""
        return self.is_active

