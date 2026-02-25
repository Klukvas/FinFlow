from __future__ import annotations

import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    Text,
    Boolean,
    Integer,
    Numeric,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class PaymentProvider(str, enum.Enum):
    WAYFORPAY = "WAYFORPAY"
    PADDLE = "PADDLE"


class PaymentPurpose(str, enum.Enum):
    SUBSCRIPTION = "SUBSCRIPTION"
    ONE_TIME = "ONE_TIME"


class PaymentStatus(str, enum.Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    CANCELED = "CANCELED"


class PaymentEventType(str, enum.Enum):
    CREATED = "CREATED"
    CALLBACK = "CALLBACK"
    STATUS_CHANGE = "STATUS_CHANGE"
    REFUND = "REFUND"
    VERIFICATION = "VERIFICATION"


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('CREATED', 'PENDING', 'PAID', 'FAILED', 'EXPIRED', 'REFUNDED', 'PARTIALLY_REFUNDED', 'CANCELED')",
            name="ck_payment_status",
        ),
        CheckConstraint(
            "provider IN ('WAYFORPAY', 'PADDLE')",
            name="ck_payment_provider",
        ),
        CheckConstraint(
            "purpose IN ('SUBSCRIPTION', 'ONE_TIME')",
            name="ck_payment_purpose",
        ),
        Index("idx_payments_user_created", "user_id", "created_at"),
        Index("idx_payments_workspace_created", "workspace_id", "created_at"),
        Index("idx_payments_status_created", "status", "created_at"),
        Index("idx_payments_order_reference", "order_reference", unique=True),
        Index("idx_payments_paddle_customer_id", "paddle_customer_id"),
        Index("idx_payments_paddle_subscription_id", "paddle_subscription_id"),
        Index("idx_payments_paddle_transaction_id", "paddle_transaction_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(SQLEnum(PaymentProvider), nullable=False, default=PaymentProvider.PADDLE)
    order_reference = Column(String(255), unique=True, nullable=False)

    user_id = Column(String(128), nullable=False)  # String to support both int and UUID
    workspace_id = Column(String(128), nullable=True)  # String to support both int and UUID

    purpose = Column(SQLEnum(PaymentPurpose), nullable=False, default=PaymentPurpose.SUBSCRIPTION)
    plan_code = Column(String(64), nullable=True)  # If purpose is SUBSCRIPTION

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="UAH")

    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.CREATED)

    provider_payment_url = Column(Text, nullable=True)
    provider_payload = Column(JSONB, nullable=True)
    provider_response = Column(JSONB, nullable=True)

    # Recurring payment support (legacy field, Paddle manages subscriptions natively)
    recurring_token = Column(String(255), nullable=True)
    is_recurring = Column(Boolean, default=False, nullable=False)

    # Paddle-specific fields
    paddle_customer_id = Column(String(255), nullable=True)
    paddle_subscription_id = Column(String(255), nullable=True)
    paddle_transaction_id = Column(String(255), nullable=True)

    paid_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)

    failure_reason = Column(Text, nullable=True)

    extra_data = Column(JSONB, nullable=True)  # Additional flexible data

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    events = relationship("PaymentEvent", back_populates="payment", cascade="all, delete-orphan")


class PaymentEvent(Base):
    __tablename__ = "payment_events"
    __table_args__ = (
        Index("idx_payment_events_payment_created", "payment_id", "created_at"),
        Index("idx_payment_events_provider_event", "provider_event_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)

    event_type = Column(SQLEnum(PaymentEventType), nullable=False)
    provider_event_id = Column(String(255), nullable=True)

    signature_valid = Column(Boolean, nullable=True)
    payload_raw = Column(JSONB, nullable=False)

    status_before = Column(String(64), nullable=True)
    status_after = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    payment = relationship("Payment", back_populates="events")


class ProcessedWebhookEvent(Base):
    """Track processed webhook events for idempotent handling"""
    __tablename__ = "processed_webhook_events"
    __table_args__ = (
        Index("idx_processed_webhook_events_event_id", "event_id", unique=True),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(255), unique=True, nullable=False)
    event_type = Column(String(128), nullable=False)
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    payload_hash = Column(String(64), nullable=False)


class PaddlePriceMap(Base):
    """Map plan codes to Paddle price IDs"""
    __tablename__ = "paddle_price_map"
    __table_args__ = (
        Index("idx_paddle_price_map_plan_code", "plan_code", unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_code = Column(String(64), unique=True, nullable=False)
    paddle_price_id = Column(String(255), nullable=False)
    billing_period = Column(String(16), nullable=False, default="monthly")
    amount = Column(Numeric(10, 2), nullable=True)  # Canonical plan price for server-side validation
    currency = Column(String(3), nullable=True, default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        Index("idx_idempotency_expires", "expires_at"),
    )

    key = Column(String(255), primary_key=True)
    scope = Column(String(64), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_body = Column(JSONB, nullable=True)
    response_status = Column(String(16), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
