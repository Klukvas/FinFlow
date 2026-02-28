from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class BankConnection(Base):
    __tablename__ = "bank_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    bank_type = Column(String(50), default="monobank")
    encrypted_token = Column(Text, nullable=False)
    client_name = Column(String(200), nullable=True)
    client_id = Column(String(100), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    linked_accounts = relationship("LinkedAccount", back_populates="connection", cascade="all, delete-orphan")
    sync_logs = relationship("SyncLog", back_populates="connection", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_bank_connections_workspace_user", "workspace_id", "user_id"),
    )
