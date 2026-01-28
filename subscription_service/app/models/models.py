from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from ..database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    period_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    features = relationship("PlanFeature", back_populates="plan", cascade="all, delete-orphan")


class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)


class PlanFeature(Base):
    __tablename__ = "plan_features"
    __table_args__ = (
        UniqueConstraint("plan_id", "feature_code", name="uq_plan_feature"),
    )

    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    feature_code = Column(String(64), ForeignKey("features.code", ondelete="CASCADE"), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    limit_value = Column(Integer, nullable=True)

    plan = relationship("Plan", back_populates="features")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("status IN ('active','past_due','canceled','paused')", name="ck_subscription_status"),
        UniqueConstraint("user_id", name="uq_subscriptions_user_id"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(String(128), nullable=False, index=True)
    plan_code = Column(String(64), ForeignKey("plans.code"), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="active")
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    
    # Recurring payment fields
    recurring_token = Column(String(255), nullable=True)  # Token for auto-renewal
    payment_provider = Column(String(32), nullable=True)  # Provider: WAYFORPAY
    last_payment_id = Column(String(128), nullable=True)  # Last successful payment ID
    next_billing_date = Column(DateTime, nullable=True)  # When next charge will occur
    auto_renew = Column(Boolean, default=True, nullable=False)  # Auto-renewal enabled
    
    # Consent fields (WayForPay compliance)
    consent_given = Column(Boolean, default=False, nullable=False)
    consent_version = Column(String(16), nullable=True)
    consent_timestamp = Column(DateTime, nullable=True)
    consent_ip_address = Column(String(45), nullable=True)
    consent_user_agent = Column(Text, nullable=True)
    
    # Cancellation fields (audit trail)
    cancellation_reason = Column(String(32), nullable=True)
    cancellation_comment = Column(Text, nullable=True)
    cancellation_ip_address = Column(String(45), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SubscriptionConsentLog(Base):
    """Immutable audit log of user consent events"""
    __tablename__ = "subscription_consent_log"

    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(128), nullable=False, index=True)
    consent_version = Column(String(16), nullable=False)
    consent_text = Column(Text, nullable=False)  # Full consent text at time of consent
    consent_language = Column(String(8), nullable=False)  # 'en', 'uk'
    consent_given_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    browser_fingerprint = Column(String(64), nullable=True)
    consent_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


