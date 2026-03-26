"""Tests for the enhanced subscription.updated webhook handler that detects
plan changes and notifies subscription_service."""

from __future__ import annotations

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from payment_service.app.models.models import ProcessedWebhookEvent


# ======================================================================
# subscription.updated -- plan change detection
# ======================================================================


class TestSubscriptionUpdatedPlanChange:
    """Verify that subscription.updated with a new price_id triggers
    plan change notification to subscription_service."""

    @pytest.mark.asyncio
    async def test_detects_plan_change_and_notifies(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """When items[0].price.id maps to a known plan, notify subscription_service."""
        # DB queries are only for idempotency and payment lookups (not price map)
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = None
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.updated",
            data={
                "id": "sub_plan_change_1",
                "customer_id": "ctm_1",
                "status": "active",
                "custom_data": {"user_id": "user_change_1"},
                "items": [{"price": {"id": "pri_test_pro"}, "quantity": 1}],
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.subscription_client.notify_payment_success.assert_awaited_once()
        call_kwargs = payment_service.subscription_client.notify_payment_success.call_args.kwargs
        assert call_kwargs["user_id"] == "user_change_1"
        assert call_kwargs["plan_code"] == "professional"
        assert call_kwargs["paddle_subscription_id"] == "sub_plan_change_1"
        assert call_kwargs["paddle_price_id"] == "pri_test_pro"

    @pytest.mark.asyncio
    async def test_uses_price_id_field_fallback(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """When items use price_id (not nested price.id), it must still resolve."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = None
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.updated",
            data={
                "id": "sub_flat_field",
                "customer_id": "ctm_1",
                "status": "active",
                "custom_data": {"user_id": "user_flat"},
                "items": [{"price_id": "pri_test_ent", "quantity": 1}],
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.subscription_client.notify_payment_success.assert_awaited_once()
        call_kwargs = payment_service.subscription_client.notify_payment_success.call_args.kwargs
        assert call_kwargs["plan_code"] == "enterprise"

    @pytest.mark.asyncio
    async def test_no_notification_when_price_not_mapped(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """When the price_id doesn't exist in the price map, skip notification."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = None
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.updated",
            data={
                "id": "sub_unknown_price",
                "customer_id": "ctm_1",
                "status": "active",
                "custom_data": {"user_id": "user_unknown"},
                "items": [{"price": {"id": "pri_unknown_xyz"}, "quantity": 1}],
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.subscription_client.notify_payment_success.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_notification_when_no_user_id(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """When custom_data has no user_id, skip notification even if price maps."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = None
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.updated",
            data={
                "id": "sub_no_user",
                "customer_id": "ctm_1",
                "status": "active",
                "custom_data": {"user_id": ""},
                "items": [{"price": {"id": "pri_test_pro"}, "quantity": 1}],
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.subscription_client.notify_payment_success.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_notification_when_no_items(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """When the webhook has no items array, skip notification."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = None
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.updated",
            data={
                "id": "sub_no_items",
                "customer_id": "ctm_1",
                "status": "active",
                "custom_data": {"user_id": "user_1"},
                "items": [],
            },
        )

        await payment_service.process_paddle_webhook(event)

        payment_service.subscription_client.notify_payment_success.assert_not_awaited()


# ======================================================================
# subscription.updated -- audit event
# ======================================================================


class TestSubscriptionUpdatedAudit:
    """Verify that subscription.updated still records audit events."""

    @pytest.mark.asyncio
    async def test_stores_audit_event_when_payment_found(
        self, payment_service, mock_db, make_webhook_event, make_payment,
    ):
        """When a related payment exists, a PaymentEvent must be stored."""
        existing_payment = make_payment(
            status="PAID",
            paddle_subscription_id="sub_audit_1",
        )

        # _find_payment_by_subscription_or_custom_data must find the payment
        def query_side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            q.order_by.return_value = q
            q.first.return_value = None
            # Return existing payment when querying by subscription_id
            if hasattr(model, '__tablename__') and getattr(model, '__tablename__', '') == 'payments':
                q.first.return_value = existing_payment
            return q

        mock_db.query.side_effect = query_side_effect

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.updated",
            data={
                "id": "sub_audit_1",
                "customer_id": "ctm_1",
                "status": "active",
                "custom_data": {"user_id": "user_1"},
                "items": [],
            },
        )

        await payment_service.process_paddle_webhook(event)

        # Audit event should have been created
        payment_service.event_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_idempotency_record_stored(
        self, payment_service, mock_db, make_webhook_event,
    ):
        """Even without a plan change, the processed event must be recorded."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.first.return_value = None
        mock_db.query.return_value = query_mock

        payment_service.event_repo.create = MagicMock()

        event = make_webhook_event(
            event_type="subscription.updated",
            event_id="evt_sub_updated_idemp",
            data={
                "id": "sub_idemp_1",
                "customer_id": "ctm_1",
                "status": "active",
                "custom_data": {"user_id": "user_1"},
                "items": [],
            },
        )

        await payment_service.process_paddle_webhook(event)

        # Verify idempotency record was stored
        add_calls = mock_db.add.call_args_list
        added_objects = [c.args[0] for c in add_calls]
        processed_events = [o for o in added_objects if isinstance(o, ProcessedWebhookEvent)]
        assert len(processed_events) == 1
        assert processed_events[0].event_id == "evt_sub_updated_idemp"
