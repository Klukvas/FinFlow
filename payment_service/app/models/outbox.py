"""Outbox event model for reliable cross-service notifications."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, Text, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from ..database import Base


class OutboxEvent(Base):
    """Outbox table for transactional notifications.

    Events are written in the same DB transaction as the business operation,
    then delivered asynchronously by the outbox processor.
    """

    __tablename__ = "outbox_events"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'delivered', 'failed')",
            name="ck_outbox_status",
        ),
        Index("idx_outbox_pending", "status", "next_retry_at"),
        Index("idx_outbox_aggregate", "aggregate_type", "aggregate_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type = Column(String(64), nullable=False)  # 'payment'
    aggregate_id = Column(UUID(as_uuid=True), nullable=False)  # payment.id
    event_type = Column(String(64), nullable=False)  # 'payment_success', 'payment_failed', etc.
    payload = Column(JSONB, nullable=False)
    destination_url = Column(String(512), nullable=False)
    headers = Column(JSONB, nullable=True)  # Additional headers (e.g., X-Internal-Token)
    status = Column(String(16), nullable=False, default="pending")
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=10)
    next_retry_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
