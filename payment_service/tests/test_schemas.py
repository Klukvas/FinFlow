"""Tests for Pydantic schemas in schemas/payment.py.

Validates field types, defaults, validators, and serialisation behaviour.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from pydantic import ValidationError as PydanticValidationError

from payment_service.app.schemas.payment import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PaymentEventOut,
    PaymentOut,
    PaddleWebhookEvent,
    ChangePlanRequest,
    ChangePlanResponse,
    RefundRequest,
    RefundResponse,
)
from payment_service.app.models.models import (
    PaymentStatus,
    PaymentProvider,
    PaymentPurpose,
)


# ======================================================================
# CreatePaymentRequest
# ======================================================================


class TestCreatePaymentRequest:
    """Tests for CreatePaymentRequest schema."""

    def test_valid_request(self):
        req = CreatePaymentRequest(
            user_id="user_1",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="professional",
            amount=Decimal("29.99"),
            currency="USD",
        )
        assert req.user_id == "user_1"
        assert req.amount == Decimal("29.99")
        assert req.currency == "USD"

    def test_currency_default_uah(self):
        req = CreatePaymentRequest(
            user_id="u1",
            purpose=PaymentPurpose.ONE_TIME,
            amount=Decimal("10.00"),
        )
        assert req.currency == "UAH"

    def test_currency_uppercased(self):
        req = CreatePaymentRequest(
            user_id="u1",
            purpose=PaymentPurpose.ONE_TIME,
            amount=Decimal("1.00"),
            currency="eur",
        )
        assert req.currency == "EUR"

    def test_invalid_currency_too_long_raises(self):
        with pytest.raises(PydanticValidationError):
            CreatePaymentRequest(
                user_id="u1",
                purpose=PaymentPurpose.ONE_TIME,
                amount=Decimal("1.00"),
                currency="USDX",
            )

    def test_invalid_currency_non_alpha_raises(self):
        with pytest.raises(PydanticValidationError):
            CreatePaymentRequest(
                user_id="u1",
                purpose=PaymentPurpose.ONE_TIME,
                amount=Decimal("1.00"),
                currency="12A",
            )

    def test_amount_must_be_positive(self):
        with pytest.raises(PydanticValidationError):
            CreatePaymentRequest(
                user_id="u1",
                purpose=PaymentPurpose.ONE_TIME,
                amount=Decimal("0"),
                currency="USD",
            )

    def test_amount_negative_raises(self):
        with pytest.raises(PydanticValidationError):
            CreatePaymentRequest(
                user_id="u1",
                purpose=PaymentPurpose.ONE_TIME,
                amount=Decimal("-5.00"),
                currency="USD",
            )

    def test_optional_fields_default_none(self):
        req = CreatePaymentRequest(
            user_id="u1",
            purpose=PaymentPurpose.ONE_TIME,
            amount=Decimal("1.00"),
        )
        assert req.workspace_id is None
        assert req.plan_code is None
        assert req.return_url is None
        assert req.metadata is None

    def test_metadata_accepts_dict(self):
        req = CreatePaymentRequest(
            user_id="u1",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="pro",
            amount=Decimal("10.00"),
            metadata={"key": "value"},
        )
        assert req.metadata == {"key": "value"}


# ======================================================================
# CreatePaymentResponse
# ======================================================================


class TestCreatePaymentResponse:
    """Tests for CreatePaymentResponse schema."""

    def test_valid_response(self):
        resp = CreatePaymentResponse(
            payment_id=uuid4(),
            order_reference="ORDER_123",
            provider=PaymentProvider.PADDLE,
            amount=Decimal("29.99"),
            currency="USD",
            status=PaymentStatus.CREATED,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.status == PaymentStatus.CREATED
        assert resp.provider == PaymentProvider.PADDLE

    def test_optional_fields_default_none(self):
        resp = CreatePaymentResponse(
            payment_id=uuid4(),
            order_reference="ORDER_456",
            provider=PaymentProvider.PADDLE,
            amount=Decimal("10"),
            currency="USD",
            status=PaymentStatus.CREATED,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.payment_url is None
        assert resp.checkout_url is None
        assert resp.transaction_id is None
        assert resp.provider_form_fields is None


# ======================================================================
# PaymentOut
# ======================================================================


class TestPaymentOut:
    """Tests for PaymentOut schema."""

    def test_valid_output(self):
        out = PaymentOut(
            id=uuid4(),
            provider=PaymentProvider.PADDLE,
            order_reference="ORDER_out",
            user_id="user_1",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="pro",
            amount=Decimal("29.99"),
            currency="USD",
            status=PaymentStatus.PAID,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert out.status == PaymentStatus.PAID

    def test_events_default_empty_list(self):
        out = PaymentOut(
            id=uuid4(),
            provider=PaymentProvider.PADDLE,
            order_reference="ORDER_events",
            user_id="u1",
            purpose=PaymentPurpose.ONE_TIME,
            amount=Decimal("5"),
            currency="USD",
            status=PaymentStatus.CREATED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert out.events == []


# ======================================================================
# PaymentEventOut
# ======================================================================


class TestPaymentEventOut:
    """Tests for PaymentEventOut schema."""

    def test_valid_event_output(self):
        evt = PaymentEventOut(
            id=uuid4(),
            payment_id=uuid4(),
            event_type="CALLBACK",
            created_at=datetime.now(timezone.utc),
        )
        assert evt.event_type == "CALLBACK"
        assert evt.provider_event_id is None
        assert evt.signature_valid is None


# ======================================================================
# PaddleWebhookEvent
# ======================================================================


class TestPaddleWebhookEvent:
    """Tests for PaddleWebhookEvent schema."""

    def test_valid_webhook_event(self):
        evt = PaddleWebhookEvent(
            event_id="evt_123",
            event_type="transaction.completed",
            occurred_at="2026-01-01T00:00:00Z",
            data={"id": "txn_1"},
        )
        assert evt.event_id == "evt_123"
        assert evt.event_type == "transaction.completed"
        assert evt.notification_id is None

    def test_with_notification_id(self):
        evt = PaddleWebhookEvent(
            event_id="evt_456",
            event_type="subscription.activated",
            occurred_at="2026-01-01T00:00:00Z",
            data={},
            notification_id="ntf_789",
        )
        assert evt.notification_id == "ntf_789"

    def test_missing_required_fields_raises(self):
        with pytest.raises(PydanticValidationError):
            PaddleWebhookEvent(
                event_type="subscription.created",
                occurred_at="2026-01-01T00:00:00Z",
                data={},
            )


# ======================================================================
# ChangePlanRequest / ChangePlanResponse
# ======================================================================


class TestChangePlanRequest:
    """Tests for ChangePlanRequest schema."""

    def test_valid_request(self):
        req = ChangePlanRequest(
            user_id="user_1",
            new_plan_code="enterprise",
            paddle_subscription_id="sub_123",
        )
        assert req.new_plan_code == "enterprise"
        assert req.metadata is None

    def test_with_metadata(self):
        req = ChangePlanRequest(
            user_id="user_1",
            new_plan_code="pro",
            paddle_subscription_id="sub_456",
            metadata={"consent_given": True},
        )
        assert req.metadata["consent_given"] is True


class TestChangePlanResponse:
    """Tests for ChangePlanResponse schema."""

    def test_valid_response(self):
        resp = ChangePlanResponse(
            success=True,
            new_plan_code="enterprise",
            paddle_subscription_id="sub_789",
        )
        assert resp.success is True
        assert resp.old_plan_code is None


# ======================================================================
# RefundRequest / RefundResponse
# ======================================================================


class TestRefundRequest:
    """Tests for RefundRequest schema."""

    def test_full_refund(self):
        req = RefundRequest()
        assert req.amount is None
        assert req.reason is None

    def test_partial_refund(self):
        req = RefundRequest(amount=Decimal("5.00"), reason="customer request")
        assert req.amount == Decimal("5.00")
        assert req.reason == "customer request"


class TestRefundResponse:
    """Tests for RefundResponse schema."""

    def test_valid_response(self):
        resp = RefundResponse(
            payment_id=uuid4(),
            status=PaymentStatus.REFUNDED,
            refunded_amount=Decimal("29.99"),
            refunded_at=datetime.now(timezone.utc),
        )
        assert resp.status == PaymentStatus.REFUNDED
