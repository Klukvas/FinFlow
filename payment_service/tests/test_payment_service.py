"""Tests for PaymentService business logic beyond what existing tests cover.

Focuses on create_recurring_payment, process_refund, helper methods,
and edge cases not tested by existing checkout/webhook/plan-change tests.
"""

from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from payment_service.app.models.models import (
    Payment,
    PaymentEvent,
    PaymentStatus,
    PaymentProvider,
    PaymentPurpose,
    PaymentEventType,
)
from payment_service.app.models.outbox import OutboxEvent
from payment_service.app.schemas.payment import CreatePaymentRequest
from payment_service.app.utils.errors import ValidationError, ConflictError


# ======================================================================
# create_recurring_payment
# ======================================================================


class TestCreateRecurringPayment:
    """Tests for PaymentService.create_recurring_payment."""

    @pytest.mark.asyncio
    async def test_creates_payment_with_correct_fields(self, payment_service, mock_db):
        payment_service.payment_repo.create = MagicMock(side_effect=lambda p: p)
        payment_service.event_repo.create = MagicMock()

        payment = await payment_service.create_recurring_payment(
            user_id="user_recurring",
            subscription_id=42,
            plan_code="professional",
            amount=Decimal("29.99"),
            currency="USD",
            recurring_token="tok_abc123",
        )

        assert payment.user_id == "user_recurring"
        assert payment.plan_code == "professional"
        assert payment.amount == Decimal("29.99")
        assert payment.currency == "USD"
        assert payment.status == PaymentStatus.CREATED
        assert payment.purpose == PaymentPurpose.SUBSCRIPTION
        assert payment.provider == PaymentProvider.PADDLE
        assert payment.extra_data["recurring_token"] == "tok_abc123"
        assert payment.extra_data["subscription_id"] == 42
        assert payment.extra_data["source"] == "scheduler"

    @pytest.mark.asyncio
    async def test_creates_payment_event(self, payment_service, mock_db):
        payment_service.payment_repo.create = MagicMock(side_effect=lambda p: p)
        payment_service.event_repo.create = MagicMock()

        await payment_service.create_recurring_payment(
            user_id="user_evt",
            subscription_id=1,
            plan_code="pro",
            amount=Decimal("10"),
            currency="USD",
            recurring_token="tok_1",
        )

        payment_service.event_repo.create.assert_called_once()
        event_arg = payment_service.event_repo.create.call_args.args[0]
        assert event_arg.event_type == PaymentEventType.CREATED

    @pytest.mark.asyncio
    async def test_missing_plan_code_raises(self, payment_service, mock_db):
        with pytest.raises(ValidationError) as exc_info:
            await payment_service.create_recurring_payment(
                user_id="u1",
                subscription_id=1,
                plan_code="",
                amount=Decimal("10"),
                currency="USD",
                recurring_token="tok_1",
            )
        assert "MISSING_PLAN_CODE" in exc_info.value.error_code

    @pytest.mark.asyncio
    async def test_missing_recurring_token_raises(self, payment_service, mock_db):
        with pytest.raises(ValidationError) as exc_info:
            await payment_service.create_recurring_payment(
                user_id="u1",
                subscription_id=1,
                plan_code="pro",
                amount=Decimal("10"),
                currency="USD",
                recurring_token="",
            )
        assert "MISSING_RECURRING_TOKEN" in exc_info.value.error_code

    @pytest.mark.asyncio
    async def test_generates_unique_order_reference(self, payment_service, mock_db):
        payment_service.payment_repo.create = MagicMock(side_effect=lambda p: p)
        payment_service.event_repo.create = MagicMock()

        p1 = await payment_service.create_recurring_payment(
            user_id="u1", subscription_id=1, plan_code="pro",
            amount=Decimal("10"), currency="USD", recurring_token="tok_1",
        )
        p2 = await payment_service.create_recurring_payment(
            user_id="u1", subscription_id=1, plan_code="pro",
            amount=Decimal("10"), currency="USD", recurring_token="tok_1",
        )

        assert p1.order_reference != p2.order_reference


# ======================================================================
# process_refund
# ======================================================================


class TestProcessRefund:
    """Tests for PaymentService.process_refund."""

    def _make_paid_payment(self) -> MagicMock:
        payment = MagicMock(spec=Payment)
        payment.id = uuid4()
        payment.status = PaymentStatus.PAID
        payment.paddle_transaction_id = "txn_test_refund"
        payment.amount = Decimal("29.99")
        payment.purpose = PaymentPurpose.SUBSCRIPTION
        payment.plan_code = "pro"
        payment.user_id = "user_refund"
        payment.workspace_id = "ws_1"
        payment.currency = "USD"
        return payment

    @pytest.mark.asyncio
    async def test_full_refund_updates_status(self, payment_service, mock_db):
        payment = self._make_paid_payment()
        payment_service.payment_repo.update_status = MagicMock(return_value=payment)
        payment_service.event_repo.create = MagicMock()
        payment_service.paddle_client.create_adjustment = AsyncMock(
            return_value={"id": "adj_1"}
        )

        result = await payment_service.process_refund(payment)

        payment_service.payment_repo.update_status.assert_called_once_with(
            payment, PaymentStatus.REFUNDED,
        )
        assert result is payment

    @pytest.mark.asyncio
    async def test_partial_refund_passes_amount_to_paddle(self, payment_service, mock_db):
        payment = self._make_paid_payment()
        payment_service.payment_repo.update_status = MagicMock(return_value=payment)
        payment_service.event_repo.create = MagicMock()
        payment_service.paddle_client.create_adjustment = AsyncMock(
            return_value={"id": "adj_2"}
        )

        await payment_service.process_refund(payment, amount=Decimal("10.00"))

        call_kwargs = payment_service.paddle_client.create_adjustment.call_args.kwargs
        assert call_kwargs["amount"] == 1000  # 10.00 * 100

    @pytest.mark.asyncio
    async def test_refund_creates_audit_event(self, payment_service, mock_db):
        payment = self._make_paid_payment()
        payment_service.payment_repo.update_status = MagicMock(return_value=payment)
        payment_service.event_repo.create = MagicMock()
        payment_service.paddle_client.create_adjustment = AsyncMock(
            return_value={"id": "adj_3"}
        )

        await payment_service.process_refund(payment, reason="customer request")

        payment_service.event_repo.create.assert_called_once()
        event_arg = payment_service.event_repo.create.call_args.args[0]
        assert event_arg.event_type == PaymentEventType.REFUND
        assert event_arg.payload_raw["reason"] == "customer request"

    @pytest.mark.asyncio
    async def test_non_paid_payment_raises(self, payment_service, mock_db):
        payment = self._make_paid_payment()
        payment.status = PaymentStatus.CREATED

        with pytest.raises(ValidationError) as exc_info:
            await payment_service.process_refund(payment)
        assert "INVALID_REFUND_STATUS" in exc_info.value.error_code

    @pytest.mark.asyncio
    async def test_missing_transaction_id_raises(self, payment_service, mock_db):
        payment = self._make_paid_payment()
        payment.paddle_transaction_id = None

        with pytest.raises(ValidationError) as exc_info:
            await payment_service.process_refund(payment)
        assert "MISSING_TRANSACTION_ID" in exc_info.value.error_code

    @pytest.mark.asyncio
    async def test_refund_queues_outbox_event(self, payment_service, mock_db):
        payment = self._make_paid_payment()
        payment_service.payment_repo.update_status = MagicMock(return_value=payment)
        payment_service.event_repo.create = MagicMock()
        payment_service.paddle_client.create_adjustment = AsyncMock(
            return_value={"id": "adj_4"}
        )

        await payment_service.process_refund(payment, reason="refund test")

        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        assert len(outbox_events) >= 1
        refund_events = [e for e in outbox_events if e.event_type == "payment_refunded"]
        assert len(refund_events) == 1
        assert refund_events[0].payload["user_id"] == "user_refund"
        assert refund_events[0].payload["reason"] == "refund test"


# ======================================================================
# create_payment -- additional edge cases
# ======================================================================


class TestCreatePaymentEdgeCases:
    """Edge cases for PaymentService.create_payment."""

    @pytest.mark.asyncio
    async def test_duplicate_payment_raises_conflict(self, payment_service, mock_db):
        """Active payment for same user+plan must raise ConflictError."""
        existing = MagicMock(spec=Payment)
        existing.id = uuid4()
        payment_service.payment_repo.get_active_payment_for_user_plan = MagicMock(
            return_value=existing,
        )

        request = CreatePaymentRequest(
            user_id="u_dup",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="professional",
            amount=Decimal("29.99"),
            currency="USD",
            metadata={
                "user_email": "dup@test.com",
                "consent_given": True,
                "consent_version": "v1.0.0",
                "consent_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        with pytest.raises(ConflictError) as exc_info:
            await payment_service.create_payment(request)
        assert "DUPLICATE_PAYMENT" in exc_info.value.error_code

    # PRICE_MISMATCH test removed — Paddle is the source of truth for pricing
    # via price_id, the frontend amount is for display only.


# ======================================================================
# Helper methods
# ======================================================================


class TestPaymentServiceHelpers:
    """Tests for private helper methods on PaymentService."""

    def test_generate_order_reference_format(self, payment_service):
        ref = payment_service._generate_order_reference()
        assert ref.startswith("ORDER_")
        parts = ref.split("_")
        assert len(parts) >= 3  # ORDER_ + timestamp + hex

    def test_generate_order_reference_unique(self, payment_service):
        refs = {payment_service._generate_order_reference() for _ in range(50)}
        assert len(refs) == 50

    def test_get_product_name_subscription(self, payment_service):
        request = MagicMock()
        request.purpose = PaymentPurpose.SUBSCRIPTION
        request.plan_code = "professional"

        name = payment_service._get_product_name(request)
        assert "professional" in name
        assert "Subscription" in name

    def test_get_product_name_one_time(self, payment_service):
        request = MagicMock()
        request.purpose = PaymentPurpose.ONE_TIME

        name = payment_service._get_product_name(request)
        assert "One-time" in name

    def test_compute_payload_hash_deterministic(self, payment_service):
        payload = {"key": "value", "nested": {"a": 1}}
        h1 = payment_service._compute_payload_hash(payload)
        h2 = payment_service._compute_payload_hash(payload)
        assert h1 == h2

    def test_compute_payload_hash_different_for_different_data(self, payment_service):
        h1 = payment_service._compute_payload_hash({"a": 1})
        h2 = payment_service._compute_payload_hash({"a": 2})
        assert h1 != h2


# ======================================================================
# _notify_payment_success (outbox integration)
# ======================================================================


class TestNotifyPaymentSuccess:
    """Tests for _notify_payment_success outbox event creation."""

    @pytest.mark.asyncio
    async def test_subscription_payment_creates_outbox_event(self, payment_service, mock_db, make_payment):
        payment = make_payment(status="PAID", plan_code="professional")

        await payment_service._notify_payment_success(
            payment,
            paddle_customer_id="ctm_1",
            paddle_subscription_id="sub_1",
            paddle_price_id="pri_1",
        )

        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        assert len(outbox_events) == 1
        assert outbox_events[0].event_type == "payment_success"
        assert outbox_events[0].payload["paddle_subscription_id"] == "sub_1"

    @pytest.mark.asyncio
    async def test_one_time_payment_skips_notification(self, payment_service, mock_db):
        payment = MagicMock(spec=Payment)
        payment.id = uuid4()
        payment.purpose = PaymentPurpose.ONE_TIME
        payment.plan_code = None

        await payment_service._notify_payment_success(payment)

        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        assert len(outbox_events) == 0

    @pytest.mark.asyncio
    async def test_subscription_without_plan_code_skips(self, payment_service, mock_db):
        payment = MagicMock(spec=Payment)
        payment.id = uuid4()
        payment.purpose = PaymentPurpose.SUBSCRIPTION
        payment.plan_code = None

        await payment_service._notify_payment_success(payment)

        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        assert len(outbox_events) == 0


# ======================================================================
# _notify_payment_failure / _notify_payment_refunded
# ======================================================================


class TestNotifyPaymentFailure:
    """Tests for _notify_payment_failure outbox event."""

    @pytest.mark.asyncio
    async def test_subscription_failure_creates_outbox_event(self, payment_service, mock_db, make_payment):
        payment = make_payment(status="FAILED")

        await payment_service._notify_payment_failure(payment, "card_declined")

        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        failure_events = [e for e in outbox_events if e.event_type == "payment_failed"]
        assert len(failure_events) == 1
        assert failure_events[0].payload["reason"] == "card_declined"

    @pytest.mark.asyncio
    async def test_one_time_failure_skips(self, payment_service, mock_db):
        payment = MagicMock(spec=Payment)
        payment.purpose = PaymentPurpose.ONE_TIME

        await payment_service._notify_payment_failure(payment, "error")

        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        assert len(outbox_events) == 0


class TestNotifyPaymentRefunded:
    """Tests for _notify_payment_refunded outbox event."""

    @pytest.mark.asyncio
    async def test_subscription_refund_creates_outbox_event(self, payment_service, mock_db, make_payment):
        payment = make_payment(status="REFUNDED")

        await payment_service._notify_payment_refunded(payment, "customer request")

        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        refund_events = [e for e in outbox_events if e.event_type == "payment_refunded"]
        assert len(refund_events) == 1

    @pytest.mark.asyncio
    async def test_one_time_refund_skips(self, payment_service, mock_db):
        payment = MagicMock(spec=Payment)
        payment.id = uuid4()
        payment.purpose = PaymentPurpose.ONE_TIME

        await payment_service._notify_payment_refunded(payment, "test")

        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        assert len(outbox_events) == 0
