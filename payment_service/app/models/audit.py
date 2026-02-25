"""Admin audit log model for tracking admin actions."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from ..database import Base


class AdminAuditLog(Base):
    """Immutable log of every admin action for compliance and debugging."""

    __tablename__ = "admin_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_user_id = Column(String(128), nullable=False, index=True)
    action = Column(String(64), nullable=False)  # e.g. "list_payments", "get_stats"
    resource_type = Column(String(64), nullable=False)  # e.g. "payment"
    resource_id = Column(String(255), nullable=True)  # Specific resource if applicable
    details = Column(JSONB, nullable=True)  # Query params, filters, etc.
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
