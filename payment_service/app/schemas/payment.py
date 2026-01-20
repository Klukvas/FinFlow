from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from ..models.models import PaymentStatus, PaymentProvider, PaymentPurpose


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
    provider_form_fields: Optional[dict[str, Any]] = None  # Form fields for POST
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


class WebhookWayForPayRequest(BaseModel):
    """WayForPay webhook/callback payload"""
    merchantAccount: str
    orderReference: str
    merchantSignature: str
    amount: Decimal
    currency: str
    authCode: Optional[str] = None
    cardPan: Optional[str] = None
    transactionStatus: str
    reasonCode: Optional[int] = None
    reason: Optional[str] = None
    createdDate: Optional[int] = None
    processingDate: Optional[int] = None
    fee: Optional[Decimal] = None
    paymentSystem: Optional[str] = None
    recToken: Optional[str] = None  # Recurring payment token
    
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
