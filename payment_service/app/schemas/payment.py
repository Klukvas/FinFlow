from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
import re
from pydantic import BaseModel, Field, ConfigDict, field_validator

from ..models.models import PaymentStatus, PaymentProvider, PaymentPurpose


_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class CreatePaymentRequest(BaseModel):
    """Request to create a new payment"""
    user_id: str
    workspace_id: Optional[str] = None
    purpose: PaymentPurpose
    plan_code: Optional[str] = None
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="UAH", max_length=3)
    return_url: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.upper()
        if not _CURRENCY_RE.match(v):
            raise ValueError("currency must be a 3-letter ISO 4217 code (e.g. USD, EUR, UAH)")
        return v

    model_config = ConfigDict(from_attributes=True)


class CreatePaymentResponse(BaseModel):
    """Response after payment creation"""
    payment_id: UUID
    order_reference: str
    provider: PaymentProvider
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_url: Optional[str] = None
    checkout_url: Optional[str] = None  # Paddle checkout URL
    transaction_id: Optional[str] = None  # Paddle transaction ID for Paddle.js overlay
    provider_form_fields: Optional[dict[str, Any]] = None  # Legacy form fields
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentEventOut(BaseModel):
    """Payment event details"""
    id: UUID
    payment_id: UUID
    event_type: str
    provider_event_id: Optional[str] = None
    signature_valid: Optional[bool] = None
    status_before: Optional[str] = None
    status_after: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentOut(BaseModel):
    """Full payment details"""
    id: UUID
    provider: PaymentProvider
    order_reference: str
    user_id: str
    workspace_id: Optional[str] = None
    purpose: PaymentPurpose
    plan_code: Optional[str] = None
    amount: Decimal
    currency: str
    status: PaymentStatus
    provider_payment_url: Optional[str] = None
    paid_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    events: list[PaymentEventOut] = []

    model_config = ConfigDict(from_attributes=True)


class PaddleWebhookEvent(BaseModel):
    """Paddle Billing webhook event payload.

    Paddle sends a JSON body with these top-level fields for every
    notification.  The ``data`` dict contains the event-specific
    payload (transaction, subscription, etc.).
    """
    event_id: str
    event_type: str
    occurred_at: str
    data: dict[str, Any]
    notification_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChangePlanRequest(BaseModel):
    """Request to change subscription plan (upgrade/downgrade)."""
    user_id: str
    new_plan_code: str
    paddle_subscription_id: str
    metadata: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ChangePlanResponse(BaseModel):
    """Response after plan change."""
    success: bool
    old_plan_code: Optional[str] = None
    new_plan_code: str
    paddle_subscription_id: str

    model_config = ConfigDict(from_attributes=True)


class RefundRequest(BaseModel):
    """Request to refund a payment"""
    amount: Optional[Decimal] = None  # If None, full refund
    reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RefundResponse(BaseModel):
    """Response after refund request"""
    payment_id: UUID
    status: PaymentStatus
    refunded_amount: Decimal
    refunded_at: datetime

    model_config = ConfigDict(from_attributes=True)
