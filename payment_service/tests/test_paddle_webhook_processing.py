"""Tests for PaymentService webhook processing -- idempotency, transaction
handlers, subscription lifecycle handlers, and unknown event types."""

from __future__ import annotations

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch, call
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from payment_service.app.models.models import (
    PaymentStatus,
    PaymentProvider,
    PaymentPurpose,
    ProcessedWebhookEvent,
)
from payment_service.app.models.outbox import OutboxEvent


# ======================================================================
# Webhook idempotency
# ======================================================================


class TestWebhookIdempotency:
    """Verify that the same Paddle event_id is only processed once."""

    @pytest.mark.asyncio
    async def test_same_event_processed_once(self, payment_service, mock_db, make_webhook_event):
        """Duplicate event_id must be skipped (returns None)."""
        event = make_webhook_event(
            event_type="transaction.completed",
            event_id="evt_duplicate_1",
            data={
                "id": "txn_abc",
                "custom_data": {
                    "user_id": "user_1",
                    "order_reference": "ORDER_123",
                    "plan_code": "professional",
                },
                "customer_id": "ctm_1",
                "subscription_id": "sub_1",
                "currency_code": "USD",
                "details": {"totals": {"total": "2999"}},
                "items": [{"price_id": "pri_1"}],
            },
        )

        # First call: flush succeeds (no IntegrityError), event not yet processed
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock

        mock_db.query.return_value = query_mock

        # Wire up payment_repo to return a payment
        existing_payment = _build_payment(status=PaymentStatus.CREATED)
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=existing_payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=existing_payment)
        payment_service.event_repo.create = MagicMock()

        result = await payment_service.process_paddle_webhook(event)
        assert result is not None  # processed the first time

        # Second call: flush raises IntegrityError (UNIQUE constraint on event_id)
        mock_db.flush.side_effect = IntegrityError("duplicate", {}, None)

        result2 = await payment_service.process_paddle_webhook(event)
        assert result2 is None  # skipped due to idempotency

        # Clean up side_effect for other tests
        mock_db.flush.side_effect = None

    @pytest.mark.asyncio
    async def test_different_events_both_processed(self, payment_service, mock_db, make_webhook_event, make_payment):
        """Different event_ids must both be processed."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        existing_payment = make_payment(status="CREATED")
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=existing_payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=existing_payment)
        payment_service.event_repo.create = MagicMock()

        event_a = make_webhook_event(
            event_type="transaction.completed",
            event_id="evt_A",
            data={
                "id": "txn_a",
                "custom_data": {"user_id": "user_1", "order_reference": "ORDER_A", "plan_code": "pro"},
                "customer_id": "ctm_1",
                "subscription_id": "sub_1",
                "currency_code": "USD",
                "details": {"totals": {"total": "2999"}},
                "items": [{"price_id": "pri_1"}],
            },
        )

        event_b = make_webhook_event(
            event_type="transaction.completed",
            event_id="evt_B",
            data={
                "id": "txn_b",
                "custom_data": {"user_id": "user_2", "order_reference": "ORDER_B", "plan_code": "pro"},
                "customer_id": "ctm_2",
                "subscription_id": "sub_2",
                "currency_code": "USD",
                "details": {"totals": {"total": "2999"}},
                "items": [{"price_id": "pri_1"}],
            },
        )

        result_a = await payment_service.process_paddle_webhook(event_a)
        result_b = await payment_service.process_paddle_webhook(event_b)

        assert result_a is not None
        assert result_b is not None

    @pytest.mark.asyncio
    async def test_processed_event_stored_in_db(self, payment_service, mock_db, make_webhook_event):
        """After processing, the event_id must be recorded for deduplication."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        event = make_webhook_event(
            event_type="subscription.created",
            event_id="evt_store_test",
            data={"id": "sub_x", "custom_data": {"user_id": "user_1"}},
        )

        payment_service.event_repo.create = MagicMock()

        await payment_service.process_paddle_webhook(event)

        # Verify db.add was called with a ProcessedWebhookEvent
        add_calls = mock_db.add.call_args_list
        added_objects = [c.args[0] for c in add_calls]
        processed_events = [o for o in added_objects if isinstance(o, ProcessedWebhookEvent)]
        assert len(processed_events) == 1
        assert processed_events[0].event_id == "evt_store_test"
        assert processed_events[0].event_type == "subscription.created"


# ======================================================================
# transaction.completed
# ======================================================================


class TestTransactionCompleted:
    """Tests for the transaction.completed webhook handler."""

    def _build_txn_completed_data(
        self,
        txn_id: str = "txn_done_1",
        user_id: str = "user_1",
        order_reference: str = "ORDER_100",
        plan_code: str = "professional",
        workspace_id: str = "ws_1",
        customer_id: str = "ctm_1",
        subscription_id: str = "sub_1",
        price_id: str = "pri_1",
        total_cents: str = "2999",
        currency: str = "USD",
    ) -> dict:
        return {
            "id": txn_id,
            "customer_id": customer_id,
            "subscription_id": subscription_id,
            "currency_code": currency,
            "details": {"totals": {"total": total_cents}},
            "items": [{"price_id": price_id, "quantity": 1}],
            "custom_data": {
                "user_id": user_id,
                "order_reference": order_reference,
                "plan_code": plan_code,
                "workspace_id": workspace_id,
            },
        }

    @pytest.mark.asyncio
    async def test_sets_payment_status_to_paid(
        self, payment_service, mock_db, make_webhook_event, make_payment,
    ):
        """transaction.completed must transition payment status to PAID."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        existing_payment = make_payment(status="CREATED", order_reference="ORDER_100")
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=existing_payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=existing_payment)
        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="transaction.completed",
            data=self._build_txn_completed_data(),
        )

        result = await payment_service.process_paddle_webhook(event)

        assert result is not None
        payment_service.payment_repo.update_status.assert_called_once_with(
            existing_payment, PaymentStatus.PAID,
        )

    @pytest.mark.asyncio
    async def test_updates_paddle_ids_on_payment(
        self, payment_service, mock_db, make_webhook_event, make_payment,
    ):
        """transaction.completed must write paddle_customer_id, subscription_id,
        and transaction_id onto the payment record."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        existing_payment = make_payment(status="CREATED", order_reference="ORDER_100")
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=existing_payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=existing_payment)
        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="transaction.completed",
            data=self._build_txn_completed_data(
                customer_id="ctm_new",
                subscription_id="sub_new",
                txn_id="txn_new",
            ),
        )

        await payment_service.process_paddle_webhook(event)

        assert existing_payment.paddle_customer_id == "ctm_new"
        assert existing_payment.paddle_subscription_id == "sub_new"
        assert existing_payment.paddle_transaction_id == "txn_new"

    @pytest.mark.asyncio
    async def test_notifies_subscription_service(
        self, payment_service, mock_db, make_webhook_event, make_payment,
    ):
        """transaction.completed must call subscription_client.notify_payment_success."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        existing_payment = make_payment(status="CREATED", order_reference="ORDER_100")
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=existing_payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=existing_payment)
        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="transaction.completed",
            data=self._build_txn_completed_data(),
        )

        await payment_service.process_paddle_webhook(event)

        # Verify outbox event was created for subscription notification
        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        assert len(outbox_events) >= 1, "Expected at least one OutboxEvent to be added"
        success_events = [e for e in outbox_events if e.event_type == "payment_success"]
        assert len(success_events) == 1
        assert success_events[0].payload["user_id"] == existing_payment.user_id
        assert success_events[0].payload["plan_code"] == existing_payment.plan_code
        assert success_events[0].payload["paddle_customer_id"] == "ctm_1"
        assert success_events[0].payload["paddle_subscription_id"] == "sub_1"
        assert success_events[0].payload["paddle_price_id"] == "pri_1"

    @pytest.mark.asyncio
    async def test_creates_payment_if_not_found(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """If no existing payment matches, a new one must be created from webhook data."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        created_payment = MagicMock()
        created_payment.id = uuid4()
        created_payment.user_id = "user_1"
        created_payment.workspace_id = "ws_1"
        created_payment.purpose = PaymentPurpose.SUBSCRIPTION
        created_payment.plan_code = "professional"
        created_payment.amount = Decimal("29.99")
        created_payment.currency = "USD"
        created_payment.status = PaymentStatus.CREATED
        created_payment.paddle_customer_id = "ctm_1"
        created_payment.paddle_subscription_id = "sub_1"
        created_payment.paddle_transaction_id = "txn_created_1"

        # get_by_order_reference returns None -> service will create
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=None)
        payment_service.payment_repo.create = MagicMock(return_value=created_payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=created_payment)
        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="transaction.completed",
            data=self._build_txn_completed_data(),
        )

        result = await payment_service.process_paddle_webhook(event)

        assert result is not None
        payment_service.payment_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_no_payment_and_no_user_id(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """When there is no existing payment and no user_id in custom_data, return None."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=None)
        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="transaction.completed",
            data={
                "id": "txn_orphan",
                "customer_id": "ctm_orphan",
                "currency_code": "USD",
                "details": {"totals": {"total": "0"}},
                "items": [],
                "custom_data": {"user_id": "", "order_reference": ""},
            },
        )

        result = await payment_service.process_paddle_webhook(event)
        assert result is None

    @pytest.mark.asyncio
    async def test_creates_payment_event_record(
        self, payment_service, mock_db, make_webhook_event, make_payment,
    ):
        """A PaymentEvent with type CALLBACK must be persisted."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        existing_payment = make_payment(status="CREATED", order_reference="ORDER_100")
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=existing_payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=existing_payment)
        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="transaction.completed",
            data=self._build_txn_completed_data(),
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.event_repo.create.assert_called_once()
        created_event = payment_service.event_repo.create.call_args.args[0]
        assert str(created_event.status_after) == PaymentStatus.PAID.value


# ======================================================================
# transaction.payment_failed
# ======================================================================


class TestTransactionPaymentFailed:
    """Tests for the transaction.payment_failed webhook handler."""

    @pytest.mark.asyncio
    async def test_sets_payment_status_to_failed(
        self, payment_service, mock_db, make_webhook_event, make_payment,
    ):
        """transaction.payment_failed must transition payment status to FAILED."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        existing_payment = make_payment(status="CREATED", order_reference="ORDER_FAIL")
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=existing_payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=existing_payment)
        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="transaction.payment_failed",
            data={
                "id": "txn_fail_1",
                "custom_data": {"order_reference": "ORDER_FAIL"},
                "payments": [{"error_code": "card_declined"}],
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.payment_repo.update_status.assert_called_once_with(
            existing_payment, PaymentStatus.FAILED, reason="card_declined",
        )

    @pytest.mark.asyncio
    async def test_notifies_subscription_service_of_failure(
        self, payment_service, mock_db, make_webhook_event, make_payment,
    ):
        """transaction.payment_failed must notify the subscription service."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        existing_payment = make_payment(status="CREATED", order_reference="ORDER_FAIL_2")
        payment_service.payment_repo.get_by_order_reference = MagicMock(return_value=existing_payment)
        payment_service.payment_repo.update_status = MagicMock(return_value=existing_payment)
        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="transaction.payment_failed",
            data={
                "id": "txn_fail_2",
                "custom_data": {"order_reference": "ORDER_FAIL_2"},
                "payments": [{"error_code": "insufficient_funds"}],
            },
        )

        await payment_service.process_paddle_webhook(event)

        # Verify outbox event was created for failure notification
        add_calls = mock_db.add.call_args_list
        outbox_events = [c.args[0] for c in add_calls if isinstance(c.args[0], OutboxEvent)]
        failure_events = [e for e in outbox_events if e.event_type == "payment_failed"]
        assert len(failure_events) == 1


# ======================================================================
# subscription.canceled
# ======================================================================


class TestSubscriptionCanceled:
    """Tests for the subscription.canceled webhook handler."""

    @pytest.mark.asyncio
    async def test_notifies_subscription_service_canceled(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """subscription.canceled must notify subscription_service with event_type='canceled'."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.canceled",
            data={
                "id": "sub_cancel_1",
                "customer_id": "ctm_1",
                "custom_data": {"user_id": "user_1"},
                "scheduled_change": {"effective_at": "2026-04-01T00:00:00Z"},
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.subscription_client.notify_paddle_subscription_event.assert_awaited_once()
        call_kwargs = payment_service.subscription_client.notify_paddle_subscription_event.call_args.kwargs
        assert call_kwargs["user_id"] == "user_1"
        assert call_kwargs["paddle_subscription_id"] == "sub_cancel_1"
        assert call_kwargs["event_type"] == "canceled"
        assert call_kwargs["effective_from"] == "2026-04-01T00:00:00Z"

    @pytest.mark.asyncio
    async def test_no_notification_when_user_id_missing(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """subscription.canceled with empty user_id must not call subscription_client."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.canceled",
            data={
                "id": "sub_cancel_no_user",
                "customer_id": "ctm_1",
                "custom_data": {"user_id": ""},
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.subscription_client.notify_paddle_subscription_event.assert_not_awaited()


# ======================================================================
# subscription.past_due
# ======================================================================


class TestSubscriptionPastDue:
    """Tests for the subscription.past_due webhook handler."""

    @pytest.mark.asyncio
    async def test_notifies_past_due(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """subscription.past_due must notify subscription_service with event_type='past_due'."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.past_due",
            data={
                "id": "sub_pastdue_1",
                "customer_id": "ctm_1",
                "custom_data": {"user_id": "user_1"},
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.subscription_client.notify_paddle_subscription_event.assert_awaited_once()
        call_kwargs = payment_service.subscription_client.notify_paddle_subscription_event.call_args.kwargs
        assert call_kwargs["event_type"] == "past_due"
        assert call_kwargs["user_id"] == "user_1"
        assert call_kwargs["paddle_subscription_id"] == "sub_pastdue_1"


# ======================================================================
# subscription.activated
# ======================================================================


class TestSubscriptionActivated:
    """Tests for the subscription.activated webhook handler."""

    @pytest.mark.asyncio
    async def test_notifies_subscription_activated(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """subscription.activated must notify subscription_service."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.activated",
            data={
                "id": "sub_active_1",
                "customer_id": "ctm_1",
                "custom_data": {"user_id": "user_1"},
                "items": [{"price_id": "pri_1"}],
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.subscription_client.notify_paddle_subscription_event.assert_awaited_once()
        call_kwargs = payment_service.subscription_client.notify_paddle_subscription_event.call_args.kwargs
        assert call_kwargs["event_type"] == "activated"


# ======================================================================
# subscription.paused
# ======================================================================


class TestSubscriptionPaused:
    """Tests for the subscription.paused webhook handler."""

    @pytest.mark.asyncio
    async def test_notifies_subscription_paused(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """subscription.paused must notify subscription_service with effective_from."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.paused",
            data={
                "id": "sub_paused_1",
                "customer_id": "ctm_1",
                "custom_data": {"user_id": "user_1"},
                "paused_at": "2026-03-15T00:00:00Z",
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.subscription_client.notify_paddle_subscription_event.assert_awaited_once()
        call_kwargs = payment_service.subscription_client.notify_paddle_subscription_event.call_args.kwargs
        assert call_kwargs["event_type"] == "paused"
        assert call_kwargs["effective_from"] == "2026-03-15T00:00:00Z"


# ======================================================================
# subscription.resumed
# ======================================================================


class TestSubscriptionResumed:
    """Tests for the subscription.resumed webhook handler."""

    @pytest.mark.asyncio
    async def test_notifies_subscription_resumed(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """subscription.resumed must notify subscription_service."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        query_mock.order_by.return_value = query_mock
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.resumed",
            data={
                "id": "sub_resumed_1",
                "customer_id": "ctm_1",
                "custom_data": {"user_id": "user_1"},
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.subscription_client.notify_paddle_subscription_event.assert_awaited_once()
        call_kwargs = payment_service.subscription_client.notify_paddle_subscription_event.call_args.kwargs
        assert call_kwargs["event_type"] == "resumed"


# ======================================================================
# Unknown event types
# ======================================================================


class TestUnknownEvent:
    """Tests for event types without a registered handler."""

    @pytest.mark.asyncio
    async def test_unknown_event_no_error(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """An unrecognised event type must not raise and must return None."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        mock_db.query.return_value = query_mock

        event = make_webhook_event(
            event_type="adjustment.created",
            data={"id": "adj_1"},
        )

        result = await payment_service.process_paddle_webhook(event)
        assert result is None

    @pytest.mark.asyncio
    async def test_unknown_event_still_records_idempotency(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """Even unknown events must be recorded to prevent duplicate processing."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        mock_db.query.return_value = query_mock

        event = make_webhook_event(
            event_type="payout.completed",
            event_id="evt_payout_1",
            data={"id": "pay_1"},
        )

        await payment_service.process_paddle_webhook(event)

        add_calls = mock_db.add.call_args_list
        added_objects = [c.args[0] for c in add_calls]
        processed_events = [o for o in added_objects if isinstance(o, ProcessedWebhookEvent)]
        assert len(processed_events) == 1
        assert processed_events[0].event_id == "evt_payout_1"


# ======================================================================
# Helpers
# ======================================================================


def _build_payment(status: PaymentStatus = PaymentStatus.CREATED):
    """Build a minimal Payment mock for tests that don't use the make_payment fixture."""
    from payment_service.app.models.models import Payment, PaymentProvider, PaymentPurpose

    payment = MagicMock(spec=Payment)
    payment.id = uuid4()
    payment.provider = PaymentProvider.PADDLE
    payment.order_reference = "ORDER_test_helper"
    payment.user_id = "user_1"
    payment.workspace_id = "ws_1"
    payment.purpose = PaymentPurpose.SUBSCRIPTION
    payment.plan_code = "professional"
    payment.amount = Decimal("29.99")
    payment.currency = "USD"
    payment.status = status
    payment.paddle_customer_id = None
    payment.paddle_subscription_id = None
    payment.paddle_transaction_id = None
    return payment
