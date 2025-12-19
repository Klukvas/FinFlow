from sqlalchemy import Column, Integer, String, DateTime, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
import enum


class WorkspaceType(str, enum.Enum):
    PERSONAL = "personal"
    SHARED = "shared"


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(Enum(WorkspaceType), nullable=False, default=WorkspaceType.PERSONAL)
    owner_user_id = Column(Integer, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    archived_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    invites = relationship("WorkspaceInvite", back_populates="workspace", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_workspaces_archived_at", "archived_at"),
    )

    @property
    def is_archived(self) -> bool:
        """Check if workspace is archived"""
        return self.archived_at is not None

