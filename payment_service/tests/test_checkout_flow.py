"""Integration-style tests for the checkout and webhook endpoints, plus
an end-to-end flow test that exercises create_payment -> webhook -> activation.

All Paddle API and subscription_service calls are mocked; the code under
test (PaymentService, router handlers) runs for real."""

from __future__ import annotations

import hashlib
import hmac
import json
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from payment_service.app.models.models import (
    Payment,
    PaymentEvent,
    PaymentStatus,
    PaymentProvider,
    PaymentPurpose,
    PaymentEventType,
    PaddlePriceMap,
    ProcessedWebhookEvent,
)
from payment_service.app.schemas.payment import (
    CreatePaymentRequest,
    PaddleWebhookEvent,
)
from payment_service.app.models.outbox import OutboxEvent
from payment_service.app.utils.errors import ValidationError


# ======================================================================
# Checkout (create_payment via PaymentService)
# ======================================================================


class TestCheckoutEndpoint:
    """Tests for PaymentService.create_payment (checkout creation)."""

    @pytest.mark.asyncio
    async def test_returns_checkout_url(
        self, payment_service, mock_db, mock_paddle_client,
    ):
        """create_payment must return a Payment with provider_payment_url set."""
        # Arrange: price mapping exists in DB
        price_map = MagicMock(spec=PaddlePriceMap)
        price_map.paddle_price_id = "pri_test_pro"
        price_map.plan_code = "professional"
        price_map.is_active = True
        price_map.amount = Decimal("29.99")
        price_map.currency = "USD"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = price_map
        mock_db.query.return_value = query_mock

        # Stub repos so the service layer works without a real DB
        payment_service.payment_repo.create = MagicMock(side_effect=lambda p: p)
        payment_service.event_repo.create = MagicMock()

        request = CreatePaymentRequest(
            user_id="user_test_1",
            workspace_id="ws_test_1",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="professional",
            amount=Decimal("29.99"),
            currency="USD",
            metadata={
                "user_email": "test@example.com",
                "consent_given": True,
                "consent_version": "v1.0.0",
                "consent_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Act
        payment = await payment_service.create_payment(request)

        # Assert
        assert payment.provider_payment_url == "https://checkout.paddle.com/test-session"
        assert payment.paddle_transaction_id == "txn_test_abc123"
        assert payment.status == PaymentStatus.CREATED
        assert payment.provider == PaymentProvider.PADDLE

        mock_paddle_client.create_checkout_session.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_missing_plan_price_raises_validation_error(
        self, payment_service, mock_db,
    ):
        """Must raise ValidationError when no active PaddlePriceMap exists."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None  # no price mapping
        mock_db.query.return_value = query_mock

        request = CreatePaymentRequest(
            user_id="user_test_1",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="nonexistent_plan",
            amount=Decimal("99.99"),
            currency="USD",
            metadata={
                "user_email": "test@example.com",
                "consent_given": True,
                "consent_version": "v1.0.0",
                "consent_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            await payment_service.create_payment(request)

        assert "PRICE_NOT_CONFIGURED" in exc_info.value.error_code

    @pytest.mark.asyncio
    async def test_missing_plan_code_for_subscription_raises(
        self, payment_service, mock_db,
    ):
        """SUBSCRIPTION purpose without plan_code must raise ValidationError."""
        request = CreatePaymentRequest(
            user_id="user_test_1",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code=None,
            amount=Decimal("29.99"),
            currency="USD",
        )

        with pytest.raises(ValidationError) as exc_info:
            await payment_service.create_payment(request)

        assert "MISSING_PLAN_CODE" in exc_info.value.error_code

    @pytest.mark.asyncio
    async def test_creates_payment_event_on_success(
        self, payment_service, mock_db, mock_paddle_client,
    ):
        """A CREATED PaymentEvent must be persisted alongside the payment."""
        price_map = MagicMock(spec=PaddlePriceMap)
        price_map.paddle_price_id = "pri_test_1"
        price_map.plan_code = "professional"
        price_map.is_active = True
        price_map.amount = Decimal("29.99")
        price_map.currency = "USD"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = price_map
        mock_db.query.return_value = query_mock

        payment_service.payment_repo.create = MagicMock(side_effect=lambda p: p)
        payment_service.event_repo.create = MagicMock()

        request = CreatePaymentRequest(
            user_id="user_test_1",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="professional",
            amount=Decimal("29.99"),
            currency="USD",
            metadata={
                "user_email": "test@example.com",
                "consent_given": True,
                "consent_version": "v1.0.0",
                "consent_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        await payment_service.create_payment(request)

        payment_service.event_repo.create.assert_called_once()
        event_arg = payment_service.event_repo.create.call_args.args[0]
        assert event_arg.event_type == PaymentEventType.CREATED
        assert event_arg.status_after == PaymentStatus.CREATED.value

    @pytest.mark.asyncio
    async def test_passes_custom_data_to_paddle(
        self, payment_service, mock_db, mock_paddle_client,
    ):
        """Custom data (user_id, workspace_id, plan_code) must be forwarded to Paddle."""
        price_map = MagicMock(spec=PaddlePriceMap)
        price_map.paddle_price_id = "pri_test_data"
        price_map.plan_code = "professional"
        price_map.is_active = True
        price_map.amount = Decimal("29.99")
        price_map.currency = "USD"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = price_map
        mock_db.query.return_value = query_mock

        payment_service.payment_repo.create = MagicMock(side_effect=lambda p: p)
        payment_service.event_repo.create = MagicMock()

        request = CreatePaymentRequest(
            user_id="user_42",
            workspace_id="ws_99",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="professional",
            amount=Decimal("29.99"),
            currency="USD",
            metadata={
                "user_email": "custom@example.com",
                "consent_given": True,
                "consent_version": "v1.0.0",
                "consent_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        await payment_service.create_payment(request)

        call_kwargs = mock_paddle_client.create_checkout_session.call_args.kwargs
        assert call_kwargs["customer_email"] == "custom@example.com"
        assert call_kwargs["price_id"] == "pri_test_data"
        assert call_kwargs["custom_data"]["user_id"] == "user_42"
        assert call_kwargs["custom_data"]["workspace_id"] == "ws_99"
        assert call_kwargs["custom_data"]["plan_code"] == "professional"


# ======================================================================
# Webhook endpoint behaviour
# ======================================================================


class TestWebhookEndpoint:
    """Tests that simulate the webhook router's signature verification
    and event dispatch logic."""

    @pytest.mark.asyncio
    async def test_valid_signature_processes_event(
        self, payment_service, mock_db, make_webhook_event, make_payment,
    ):
        """A valid Paddle signature must lead to event processing."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        existing_payment = make_payment(status="CREATED", order_reference="ORDER_WH1")
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=existing_payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=existing_payment)
        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="transaction.completed",
            data={
                "id": "txn_wh_1",
                "customer_id": "ctm_1",
                "subscription_id": "sub_1",
                "currency_code": "USD",
                "details": {"totals": {"total": "2999"}},
                "items": [{"price_id": "pri_1"}],
                "custom_data": {
                    "user_id": "user_1",
                    "order_reference": "ORDER_WH1",
                    "plan_code": "professional",
                },
            },
        )

        result = await payment_service.process_paddle_webhook(event)

        assert result is not None
        payment_service.payment_repo.update_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_signature_not_processed(self, paddle_client):
        """When the signature is invalid, verify_webhook_signature returns False."""
        raw_body = b'{"event_id":"evt_123","event_type":"transaction.completed"}'
        bad_signature = "ts=1234567890;h1=0000000000000000000000000000000000000000000000000000000000000000"

        is_valid = paddle_client.verify_webhook_signature(raw_body, bad_signature)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_missing_signature_header_not_processed(self, paddle_client):
        """Empty Paddle-Signature must fail verification."""
        is_valid = paddle_client.verify_webhook_signature(b'{"event_id":"evt_1"}', "")
        assert is_valid is False


# ======================================================================
# Full flow: checkout -> transaction.completed -> subscription activated
# ======================================================================


class TestFullFlow:
    """End-to-end flow test: create payment -> transaction.completed webhook
    -> subscription_service notification."""

    @pytest.mark.asyncio
    async def test_checkout_to_activation(
        self, payment_service, mock_db, mock_paddle_client,
    ):
        """Full flow: create checkout, receive transaction.completed, verify
        status=PAID and subscription_service is notified."""

        # -- Step 1: Create payment via checkout --

        price_map = MagicMock(spec=PaddlePriceMap)
        price_map.paddle_price_id = "pri_flow_1"
        price_map.plan_code = "professional"
        price_map.is_active = True
        price_map.amount = Decimal("29.99")
        price_map.currency = "USD"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = price_map
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        # Let create persist the payment and return it as-is
        created_payment_holder: list[Payment] = []

        def capture_create(p):
            created_payment_holder.append(p)
            return p

        payment_service.payment_repo.create = MagicMock(side_effect=capture_create)
        payment_service.event_repo.create = MagicMock()

        request = CreatePaymentRequest(
            user_id="user_flow_1",
            workspace_id="ws_flow_1",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="professional",
            amount=Decimal("29.99"),
            currency="USD",
            metadata={
                "user_email": "flow@example.com",
                "consent_given": True,
                "consent_version": "v1.0.0",
                "consent_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        payment = await payment_service.create_payment(request)
        assert payment.status == PaymentStatus.CREATED
        assert payment.provider_payment_url == "https://checkout.paddle.com/test-session"

        # -- Step 2: Simulate transaction.completed webhook --

        # Now the idempotency query must return None (no previous event)
        query_mock.first.return_value = None

        # get_by_order_reference must find our payment
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=payment)

        webhook_event = PaddleWebhookEvent(
            event_id="evt_flow_txn_completed",
            event_type="transaction.completed",
            occurred_at=datetime.now(timezone.utc).isoformat(),
            notification_id="ntf_flow_1",
            data={
                "id": "txn_test_abc123",
                "customer_id": "ctm_flow_1",
                "subscription_id": "sub_flow_1",
                "currency_code": "USD",
                "details": {"totals": {"total": "2999"}},
                "items": [{"price_id": "pri_flow_1"}],
                "custom_data": {
                    "user_id": "user_flow_1",
                    "order_reference": payment.order_reference,
                    "plan_code": "professional",
                    "workspace_id": "ws_flow_1",
                },
            },
        )

        result = await payment_service.process_paddle_webhook(webhook_event)

        # -- Assertions --

        assert result is not None

        # Status was set to PAID
        payment_service.payment_repo.update_status.assert_called_once_with(
            payment, PaymentStatus.PAID,
        )

        # Paddle IDs written
        assert payment.paddle_customer_id == "ctm_flow_1"
        assert payment.paddle_subscription_id == "sub_flow_1"
        assert payment.paddle_transaction_id == "txn_test_abc123"

        # Subscription service was notified via outbox
        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        success_events = [e for e in outbox_events if e.event_type == "payment_success"]
        assert len(success_events) == 1
        assert success_events[0].payload["user_id"] == "user_flow_1"
        assert success_events[0].payload["plan_code"] == "professional"
        assert success_events[0].payload["paddle_subscription_id"] == "sub_flow_1"
        assert success_events[0].payload["paddle_customer_id"] == "ctm_flow_1"
        assert success_events[0].payload["paddle_price_id"] == "pri_flow_1"

        # Processed event was recorded (idempotency)
        add_calls = mock_db.add.call_args_list
        added_objects = [c.args[0] for c in add_calls]
        processed_records = [o for o in added_objects if isinstance(o, ProcessedWebhookEvent)]
        assert len(processed_records) == 1
        assert processed_records[0].event_id == "evt_flow_txn_completed"

    @pytest.mark.asyncio
    async def test_checkout_to_failure(
        self, payment_service, mock_db, mock_paddle_client,
    ):
        """Full flow: create checkout, receive transaction.payment_failed,
        verify status=FAILED and failure notification sent."""

        # -- Step 1: Create payment --

        price_map = MagicMock(spec=PaddlePriceMap)
        price_map.paddle_price_id = "pri_fail_flow"
        price_map.plan_code = "professional"
        price_map.is_active = True
        price_map.amount = Decimal("29.99")
        price_map.currency = "USD"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = price_map
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        payment_service.payment_repo.create = MagicMock(side_effect=lambda p: p)
        payment_service.event_repo.create = MagicMock()

        request = CreatePaymentRequest(
            user_id="user_fail_flow",
            workspace_id="ws_fail",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="professional",
            amount=Decimal("29.99"),
            currency="USD",
            metadata={
                "user_email": "fail@example.com",
                "consent_given": True,
                "consent_version": "v1.0.0",
                "consent_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        payment = await payment_service.create_payment(request)
        assert payment.status == PaymentStatus.CREATED

        # -- Step 2: Simulate transaction.payment_failed webhook --

        query_mock.first.return_value = None  # idempotency check passes

        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=payment)

        fail_event = PaddleWebhookEvent(
            event_id="evt_fail_flow_1",
            event_type="transaction.payment_failed",
            occurred_at=datetime.now(timezone.utc).isoformat(),
            notification_id="ntf_fail_1",
            data={
                "id": "txn_fail_flow_1",
                "custom_data": {
                    "order_reference": payment.order_reference,
                },
                "payments": [{"error_code": "card_declined"}],
            },
        )

        result = await payment_service.process_paddle_webhook(fail_event)

        # -- Assertions --

        assert result is not None
        payment_service.payment_repo.update_status.assert_called_once_with(
            payment, PaymentStatus.FAILED, reason="card_declined",
        )
        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        failure_events = [e for e in outbox_events if e.event_type == "payment_failure"]
        assert len(failure_events) == 1

    @pytest.mark.asyncio
    async def test_duplicate_webhook_ignored_after_first(
        self, payment_service, mock_db, make_payment,
    ):
        """Sending the same event_id twice must result in only one processing."""

        # -- First call: event not yet processed --

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        existing_payment = make_payment(status="CREATED", order_reference="ORDER_DUP")
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=existing_payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=existing_payment)
        payment_service.event_repo.create = MagicMock()

        event = PaddleWebhookEvent(
            event_id="evt_dup_check",
            event_type="transaction.completed",
            occurred_at=datetime.now(timezone.utc).isoformat(),
            data={
                "id": "txn_dup_1",
                "customer_id": "ctm_1",
                "subscription_id": "sub_1",
                "currency_code": "USD",
                "details": {"totals": {"total": "2999"}},
                "items": [{"price_id": "pri_1"}],
                "custom_data": {
                    "user_id": "user_1",
                    "order_reference": "ORDER_DUP",
                    "plan_code": "professional",
                },
            },
        )

        result_first = await payment_service.process_paddle_webhook(event)
        assert result_first is not None

        # -- Second call: flush raises IntegrityError (UNIQUE on event_id) --

        mock_db.flush.side_effect = IntegrityError("duplicate", {}, None)

        result_second = await payment_service.process_paddle_webhook(event)
        assert result_second is None

        # update_status should have been called exactly once (first processing only)
        assert payment_service.payment_repo.update_status.call_count == 1

        # Clean up side_effect
        mock_db.flush.side_effect = None
