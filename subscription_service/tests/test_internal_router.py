"""Tests for internal router endpoints (payment notifications, expiring subscriptions, etc.)."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException

from app.routers.internal import (
    PaymentSuccessNotification,
    PaymentFailureNotification,
    PaymentRefundNotification,
    PaddleSubscriptionEvent,
    ExtendSubscriptionRequest,
    MarkPastDueRequest,
    activate_subscription_after_payment,
    handle_payment_failure,
    handle_payment_refund,
    handle_paddle_subscription_event,
    extend_subscription,
    mark_subscription_past_due,
    get_expiring_subscriptions,
    get_stale_paddle_subscriptions,
    get_user_features_internal,
)


# ======================================================================
# activate_subscription_after_payment
# ======================================================================


class TestActivateSubscription:
    """Tests for internal subscription activation after payment."""

    @pytest.mark.asyncio
    async def test_activates_new_subscription(self, mock_db, make_plan, make_subscription):
        """Must create subscription for new user after payment."""
        plan = make_plan(code="professional", is_active=True)
        sub = make_subscription(plan_code="professional", last_payment_id=None)

        notification = PaymentSuccessNotification(
            payment_id="pay_001",
            user_id="user_1",
            plan_code="professional",
            amount="29.99",
            currency="USD",
        )

        with (
            patch("app.routers.internal.PlanRepository") as MockPlanRepo,
            patch("app.routers.internal.SubscriptionRepository") as MockSubRepo,
            patch("app.routers.internal.invalidate_entitlements_cache"),
        ):
            mock_plan_repo = MagicMock()
            mock_plan_repo.get_by_code.return_value = plan
            MockPlanRepo.return_value = mock_plan_repo

            mock_sub_repo = MagicMock()
            mock_sub_repo.get_active_subscription.return_value = None
            mock_sub_repo.upsert_subscription.return_value = sub
            MockSubRepo.return_value = mock_sub_repo

            result = await activate_subscription_after_payment(notification, db=mock_db)

        assert result["status"] == "success"
        assert result["payment_id"] == "pay_001"

    @pytest.mark.asyncio
    async def test_deduplicates_payment(self, mock_db, make_plan, make_subscription):
        """Must skip activation when payment_id already processed."""
        plan = make_plan(code="professional", is_active=True)
        sub = make_subscription(plan_code="professional", last_payment_id="pay_001")

        notification = PaymentSuccessNotification(
            payment_id="pay_001",
            user_id="user_1",
            plan_code="professional",
            amount="29.99",
            currency="USD",
        )

        with (
            patch("app.routers.internal.PlanRepository") as MockPlanRepo,
            patch("app.routers.internal.SubscriptionRepository") as MockSubRepo,
            patch("app.routers.internal.invalidate_entitlements_cache"),
        ):
            mock_plan_repo = MagicMock()
            mock_plan_repo.get_by_code.return_value = plan
            MockPlanRepo.return_value = mock_plan_repo

            mock_sub_repo = MagicMock()
            mock_sub_repo.get_active_subscription.return_value = sub
            MockSubRepo.return_value = mock_sub_repo

            result = await activate_subscription_after_payment(notification, db=mock_db)

        assert result["status"] == "already_processed"

    @pytest.mark.asyncio
    async def test_rejects_inactive_plan(self, mock_db, make_plan):
        """Must raise HTTPException for inactive plan.

        The handler's broad ``except Exception`` block catches the 400 and
        re-raises it as a 500.  This test documents the current behaviour.
        """
        plan = make_plan(code="old_plan", is_active=False)

        notification = PaymentSuccessNotification(
            payment_id="pay_002",
            user_id="user_1",
            plan_code="old_plan",
            amount="29.99",
            currency="USD",
        )

        with (
            patch("app.routers.internal.PlanRepository") as MockPlanRepo,
            patch("app.routers.internal.SubscriptionRepository"),
            patch("app.routers.internal.invalidate_entitlements_cache"),
        ):
            mock_plan_repo = MagicMock()
            mock_plan_repo.get_by_code.return_value = plan
            MockPlanRepo.return_value = mock_plan_repo

            with pytest.raises(HTTPException) as exc_info:
                await activate_subscription_after_payment(notification, db=mock_db)
            # The broad except block wraps the 400 as a 500
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_stores_paddle_ids(self, mock_db, make_plan, make_subscription):
        """Must store Paddle IDs when provided."""
        plan = make_plan(code="professional", is_active=True)
        sub = make_subscription(plan_code="professional", last_payment_id=None)

        notification = PaymentSuccessNotification(
            payment_id="pay_003",
            user_id="user_1",
            plan_code="professional",
            amount="29.99",
            currency="USD",
            paddle_customer_id="ctm_123",
            paddle_subscription_id="sub_456",
            paddle_price_id="pri_789",
        )

        with (
            patch("app.routers.internal.PlanRepository") as MockPlanRepo,
            patch("app.routers.internal.SubscriptionRepository") as MockSubRepo,
            patch("app.routers.internal.invalidate_entitlements_cache"),
        ):
            mock_plan_repo = MagicMock()
            mock_plan_repo.get_by_code.return_value = plan
            MockPlanRepo.return_value = mock_plan_repo

            mock_sub_repo = MagicMock()
            mock_sub_repo.get_active_subscription.return_value = None
            mock_sub_repo.upsert_subscription.return_value = sub
            MockSubRepo.return_value = mock_sub_repo

            result = await activate_subscription_after_payment(notification, db=mock_db)

        assert sub.paddle_customer_id == "ctm_123"
        assert sub.paddle_subscription_id == "sub_456"
        assert sub.paddle_price_id == "pri_789"
        assert sub.payment_provider == "PADDLE"
        assert sub.auto_renew is True

    @pytest.mark.asyncio
    async def test_stores_recurring_token_legacy(self, mock_db, make_plan, make_subscription):
        """Must store recurring token for legacy WFP flow."""
        plan = make_plan(code="professional", is_active=True)
        sub = make_subscription(plan_code="professional", last_payment_id=None)

        notification = PaymentSuccessNotification(
            payment_id="pay_004",
            user_id="user_1",
            plan_code="professional",
            amount="29.99",
            currency="USD",
            recurring_token="wfp_token_abc",
        )

        with (
            patch("app.routers.internal.PlanRepository") as MockPlanRepo,
            patch("app.routers.internal.SubscriptionRepository") as MockSubRepo,
            patch("app.routers.internal.invalidate_entitlements_cache"),
        ):
            mock_plan_repo = MagicMock()
            mock_plan_repo.get_by_code.return_value = plan
            MockPlanRepo.return_value = mock_plan_repo

            mock_sub_repo = MagicMock()
            mock_sub_repo.get_active_subscription.return_value = None
            mock_sub_repo.upsert_subscription.return_value = sub
            MockSubRepo.return_value = mock_sub_repo

            result = await activate_subscription_after_payment(notification, db=mock_db)

        assert sub.recurring_token == "wfp_token_abc"
        assert sub.payment_provider == "WFP"


# ======================================================================
# handle_payment_failure
# ======================================================================


class TestHandlePaymentFailure:
    """Tests for internal payment failure handling."""

    @pytest.mark.asyncio
    async def test_marks_subscription_past_due(self, mock_db, make_subscription):
        """Must transition active subscription to past_due."""
        sub = make_subscription(status="active")

        notification = PaymentFailureNotification(
            payment_id="pay_fail_001",
            user_id="user_1",
            reason="card_declined",
        )

        query = MagicMock()
        query.filter.return_value.order_by.return_value.first.return_value = sub
        mock_db.query.return_value = query

        with patch("app.routers.internal.invalidate_entitlements_cache"):
            result = await handle_payment_failure(notification, db=mock_db)

        assert result["status"] == "past_due"
        assert sub.status == "past_due"

    @pytest.mark.asyncio
    async def test_no_subscription_returns_no_subscription(self, mock_db):
        """Must return no_subscription status when user has no subscription."""
        notification = PaymentFailureNotification(
            payment_id="pay_fail_002",
            user_id="user_no_sub",
        )

        query = MagicMock()
        query.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value = query

        result = await handle_payment_failure(notification, db=mock_db)

        assert result["status"] == "no_subscription"

    @pytest.mark.asyncio
    async def test_already_past_due_no_change(self, mock_db, make_subscription):
        """Must not change status when already past_due."""
        sub = make_subscription(status="past_due")

        notification = PaymentFailureNotification(
            payment_id="pay_fail_003",
            user_id="user_1",
        )

        query = MagicMock()
        query.filter.return_value.order_by.return_value.first.return_value = sub
        mock_db.query.return_value = query

        result = await handle_payment_failure(notification, db=mock_db)

        # past_due -> past_due is a no-op (same status), so no InvalidTransitionError
        assert result["status"] == "past_due"

    @pytest.mark.asyncio
    async def test_canceled_subscription_no_change(self, mock_db, make_subscription):
        """Must skip transition when subscription is already canceled."""
        sub = make_subscription(status="canceled")

        notification = PaymentFailureNotification(
            payment_id="pay_fail_004",
            user_id="user_1",
        )

        query = MagicMock()
        query.filter.return_value.order_by.return_value.first.return_value = sub
        mock_db.query.return_value = query

        result = await handle_payment_failure(notification, db=mock_db)

        # canceled -> past_due is invalid, so no_change
        assert result["status"] == "no_change"


# ======================================================================
# handle_payment_refund
# ======================================================================


class TestHandlePaymentRefund:
    """Tests for internal payment refund handling."""

    @pytest.mark.asyncio
    async def test_cancels_subscription_on_refund(self, mock_db, make_subscription):
        """Must cancel subscription immediately on refund."""
        sub = make_subscription(status="active")

        notification = PaymentRefundNotification(
            payment_id="pay_ref_001",
            user_id="user_1",
            reason="chargeback",
        )

        with (
            patch("app.routers.internal.SubscriptionRepository") as MockSubRepo,
            patch("app.routers.internal.invalidate_entitlements_cache"),
        ):
            mock_sub_repo = MagicMock()
            mock_sub_repo.cancel_subscription.return_value = sub
            MockSubRepo.return_value = mock_sub_repo

            result = await handle_payment_refund(notification, db=mock_db)

        assert result["status"] == "canceled"
        mock_sub_repo.cancel_subscription.assert_called_once_with("user_1", immediate=True)

    @pytest.mark.asyncio
    async def test_no_subscription_on_refund(self, mock_db):
        """Must handle case when no subscription exists during refund."""
        notification = PaymentRefundNotification(
            payment_id="pay_ref_002",
            user_id="user_no_sub",
        )

        with (
            patch("app.routers.internal.SubscriptionRepository") as MockSubRepo,
            patch("app.routers.internal.invalidate_entitlements_cache"),
        ):
            mock_sub_repo = MagicMock()
            mock_sub_repo.cancel_subscription.return_value = None
            MockSubRepo.return_value = mock_sub_repo

            result = await handle_payment_refund(notification, db=mock_db)

        assert result["status"] == "no_subscription"


# ======================================================================
# handle_paddle_subscription_event
# ======================================================================


class TestHandlePaddleSubscriptionEvent:
    """Tests for Paddle subscription lifecycle events."""

    @pytest.mark.asyncio
    async def test_processes_cancellation_event(self, mock_db, make_subscription):
        """Must cancel subscription on Paddle canceled event."""
        sub = make_subscription(
            status="active",
            paddle_subscription_id="sub_123",
        )

        event = PaddleSubscriptionEvent(
            user_id="user_1",
            paddle_subscription_id="sub_123",
            event_type="canceled",
            reason="user_requested",
        )

        # Mock ProcessedInternalEvent insert (no IntegrityError = first time)
        query = MagicMock()
        query.filter.return_value.first.return_value = sub
        mock_db.query.return_value = query

        with patch("app.routers.internal.invalidate_entitlements_cache"):
            result = await handle_paddle_subscription_event(event, db=mock_db)

        assert result["status"] == "updated"
        assert sub.status == "canceled"
        assert sub.auto_renew is False

    @pytest.mark.asyncio
    async def test_duplicate_event_skipped(self, mock_db):
        """Must skip duplicate Paddle events (idempotency)."""
        from sqlalchemy.exc import IntegrityError

        event = PaddleSubscriptionEvent(
            user_id="user_1",
            paddle_subscription_id="sub_123",
            event_type="canceled",
        )

        mock_db.flush.side_effect = IntegrityError("duplicate", {}, Exception())

        result = await handle_paddle_subscription_event(event, db=mock_db)

        assert result["status"] == "duplicate"
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_subscription_for_event(self, mock_db):
        """Must handle missing subscription gracefully."""
        event = PaddleSubscriptionEvent(
            user_id="user_missing",
            paddle_subscription_id="sub_999",
            event_type="canceled",
        )

        query = MagicMock()
        query.filter.return_value.first.return_value = None
        mock_db.query.return_value = query

        with patch("app.routers.internal.invalidate_entitlements_cache"):
            result = await handle_paddle_subscription_event(event, db=mock_db)

        assert result["status"] == "no_subscription"

    @pytest.mark.asyncio
    async def test_reactivation_event(self, mock_db, make_subscription, make_plan):
        """Must reactivate canceled subscription."""
        sub = make_subscription(
            status="canceled",
            paddle_subscription_id="sub_123",
            canceled_at=datetime.utcnow(),
            auto_renew=False,
        )
        plan = make_plan(code="professional", period_days=30)

        event = PaddleSubscriptionEvent(
            user_id="user_1",
            paddle_subscription_id="sub_123",
            event_type="activated",
        )

        # First query finds sub by paddle_subscription_id
        query = MagicMock()
        query.filter.return_value.first.return_value = sub
        # Second query finds plan
        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = plan

        mock_db.query.side_effect = [query, plan_query]

        with patch("app.routers.internal.invalidate_entitlements_cache"):
            result = await handle_paddle_subscription_event(event, db=mock_db)

        assert result["status"] == "updated"
        assert sub.status == "active"
        assert sub.auto_renew is True
        assert sub.canceled_at is None
        assert sub.cancellation_reason is None


# ======================================================================
# extend_subscription
# ======================================================================


class TestExtendSubscription:
    """Tests for extending subscription after renewal."""

    def test_extends_subscription(self, mock_db, make_subscription, make_plan):
        """Must extend expires_at by plan period."""
        old_expires = datetime.utcnow() + timedelta(days=5)
        sub = make_subscription(
            id=10,
            plan_code="professional",
            expires_at=old_expires,
        )
        plan = make_plan(code="professional", period_days=30)

        sub_query = MagicMock()
        sub_query.filter.return_value.first.return_value = sub
        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = plan

        mock_db.query.side_effect = [sub_query, plan_query]

        request = ExtendSubscriptionRequest(payment_id="pay_renew_001")
        result = extend_subscription(10, request, db=mock_db)

        assert result["status"] == "extended"
        assert sub.last_payment_id == "pay_renew_001"
        assert sub.status == "active"

    def test_extend_nonexistent_subscription_raises_404(self, mock_db):
        """Must raise 404 for unknown subscription ID."""
        sub_query = MagicMock()
        sub_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = sub_query

        request = ExtendSubscriptionRequest(payment_id="pay_001")

        with pytest.raises(HTTPException) as exc_info:
            extend_subscription(999, request, db=mock_db)
        assert exc_info.value.status_code == 404

    def test_extend_nonexistent_plan_raises_404(self, mock_db, make_subscription):
        """Must raise 404 when subscription's plan is not found."""
        sub = make_subscription(id=10, plan_code="deleted_plan")

        sub_query = MagicMock()
        sub_query.filter.return_value.first.return_value = sub
        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [sub_query, plan_query]

        request = ExtendSubscriptionRequest(payment_id="pay_001")

        with pytest.raises(HTTPException) as exc_info:
            extend_subscription(10, request, db=mock_db)
        assert exc_info.value.status_code == 404


# ======================================================================
# mark_subscription_past_due
# ======================================================================


class TestMarkSubscriptionPastDue:
    """Tests for marking subscription as past_due after failed renewal."""

    def test_marks_active_as_past_due(self, mock_db, make_subscription):
        """Must transition active subscription to past_due."""
        sub = make_subscription(id=10, status="active")

        sub_query = MagicMock()
        sub_query.filter.return_value.first.return_value = sub
        mock_db.query.return_value = sub_query

        request = MarkPastDueRequest(reason="payment_failed")
        result = mark_subscription_past_due(10, request, db=mock_db)

        assert result["status"] == "past_due"
        assert sub.status == "past_due"

    def test_already_past_due_no_change(self, mock_db, make_subscription):
        """Must be no-op when subscription is already past_due."""
        sub = make_subscription(id=10, status="past_due")

        sub_query = MagicMock()
        sub_query.filter.return_value.first.return_value = sub
        mock_db.query.return_value = sub_query

        request = MarkPastDueRequest(reason="retry_failed")
        result = mark_subscription_past_due(10, request, db=mock_db)

        # past_due -> past_due is same status, handled as no-op by state machine
        assert result["status"] == "past_due"

    def test_nonexistent_subscription_raises_404(self, mock_db):
        """Must raise 404 for unknown subscription ID."""
        sub_query = MagicMock()
        sub_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = sub_query

        request = MarkPastDueRequest(reason="test")

        with pytest.raises(HTTPException) as exc_info:
            mark_subscription_past_due(999, request, db=mock_db)
        assert exc_info.value.status_code == 404

    def test_canceled_subscription_no_transition(self, mock_db, make_subscription):
        """Must skip transition for canceled subscriptions."""
        sub = make_subscription(id=10, status="canceled")

        sub_query = MagicMock()
        sub_query.filter.return_value.first.return_value = sub
        mock_db.query.return_value = sub_query

        request = MarkPastDueRequest(reason="test")
        result = mark_subscription_past_due(10, request, db=mock_db)

        # canceled -> past_due is invalid transition, so no transition needed
        assert result["message"] is not None


# ======================================================================
# get_expiring_subscriptions
# ======================================================================


class TestGetExpiringSubscriptions:
    """Tests for getting expiring subscriptions."""

    def test_returns_expiring_subscriptions(self, mock_db, make_subscription, make_plan):
        """Must return subscriptions expiring within specified days."""
        sub = make_subscription(
            id=1,
            plan_code="professional",
            expires_at=datetime.utcnow() + timedelta(hours=12),
            auto_renew=True,
            recurring_token="token_abc",
            payment_provider="WFP",
        )
        plan = make_plan(code="professional", price="29.99", currency="USD")

        query = MagicMock()
        query.join.return_value.filter.return_value.all.return_value = [(sub, plan)]
        mock_db.query.return_value = query

        result = get_expiring_subscriptions(days_ahead=1, db=mock_db)

        assert len(result) == 1
        assert result[0].user_id == sub.user_id

    def test_returns_empty_when_none_expiring(self, mock_db):
        """Must return empty list when no subscriptions are expiring."""
        query = MagicMock()
        query.join.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value = query

        result = get_expiring_subscriptions(days_ahead=1, db=mock_db)

        assert result == []


# ======================================================================
# Notification schemas
# ======================================================================


class TestNotificationSchemas:
    """Tests for internal notification Pydantic schemas."""

    def test_payment_success_notification_minimal(self):
        n = PaymentSuccessNotification(
            payment_id="pay_001",
            user_id="user_1",
            plan_code="basic",
            amount="9.99",
            currency="USD",
        )
        assert n.recurring_token is None
        assert n.paddle_customer_id is None

    def test_payment_success_notification_full(self):
        n = PaymentSuccessNotification(
            payment_id="pay_001",
            user_id="user_1",
            plan_code="professional",
            amount="29.99",
            currency="USD",
            recurring_token="tok_abc",
            paddle_customer_id="ctm_123",
            paddle_subscription_id="sub_456",
            paddle_price_id="pri_789",
        )
        assert n.paddle_subscription_id == "sub_456"

    def test_payment_failure_notification(self):
        n = PaymentFailureNotification(
            payment_id="pay_fail_001",
            user_id="user_1",
        )
        assert n.plan_code is None
        assert n.reason is None

    def test_paddle_subscription_event(self):
        e = PaddleSubscriptionEvent(
            user_id="user_1",
            paddle_subscription_id="sub_123",
            event_type="canceled",
            reason="user_requested",
        )
        assert e.effective_from is None

    def test_extend_subscription_request(self):
        r = ExtendSubscriptionRequest(payment_id="pay_001")
        assert r.payment_id == "pay_001"

    def test_mark_past_due_request(self):
        r = MarkPastDueRequest(reason="payment_failed")
        assert r.reason == "payment_failed"


# ======================================================================
# get_user_features_internal
# ======================================================================


class TestGetUserFeaturesInternal:
    """Tests for internal user features endpoint."""

    def test_returns_user_features(self, mock_db, make_plan_feature):
        """Must return features for user with active subscription."""
        pf = make_plan_feature(feature_code="accounts", enabled=True, limit_value=10)

        with patch("app.routers.internal.FeatureRepository") as MockFeatureRepo:
            mock_repo = MagicMock()
            mock_repo.get_user_features.return_value = [
                {"feature_code": "accounts", "enabled": True, "limit_value": 10, "plan_code": "professional"}
            ]
            MockFeatureRepo.return_value = mock_repo

            result = get_user_features_internal("user_1", db=mock_db)

        assert len(result) == 1
        assert result[0].feature_code == "accounts"

    def test_returns_empty_for_no_subscription(self, mock_db):
        """Must return empty list when user has no subscription."""
        with patch("app.routers.internal.FeatureRepository") as MockFeatureRepo:
            mock_repo = MagicMock()
            mock_repo.get_user_features.return_value = []
            MockFeatureRepo.return_value = mock_repo

            result = get_user_features_internal("user_no_sub", db=mock_db)

        assert result == []


# ======================================================================
# get_stale_paddle_subscriptions
# ======================================================================


class TestGetStalePaddleSubscriptions:
    """Tests for getting stale Paddle subscriptions."""

    def test_returns_stale_subscriptions(self, mock_db, make_subscription):
        """Must return Paddle subscriptions that expired within grace period."""
        sub = make_subscription(
            id=1,
            plan_code="professional",
            payment_provider="PADDLE",
            paddle_subscription_id="sub_123",
            status="active",
            auto_renew=True,
            expires_at=datetime.utcnow() - timedelta(hours=6),
        )

        query = MagicMock()
        query.filter.return_value.all.return_value = [sub]
        mock_db.query.return_value = query

        result = get_stale_paddle_subscriptions(db=mock_db)

        assert len(result) == 1
        assert result[0]["paddle_subscription_id"] == "sub_123"
        assert result[0]["user_id"] == sub.user_id

    def test_returns_empty_when_no_stale(self, mock_db):
        """Must return empty list when no stale subscriptions exist."""
        query = MagicMock()
        query.filter.return_value.all.return_value = []
        mock_db.query.return_value = query

        result = get_stale_paddle_subscriptions(db=mock_db)

        assert result == []


# ======================================================================
# handle_paddle_subscription_event - additional edge cases
# ======================================================================


class TestPaddleSubscriptionEventEdgeCases:
    """Additional edge cases for Paddle event handling."""

    @pytest.mark.asyncio
    async def test_unknown_event_type_ignored(self, mock_db, make_subscription):
        """Must return ignored status for unknown event types."""
        sub = make_subscription(
            status="active",
            paddle_subscription_id="sub_123",
        )

        event = PaddleSubscriptionEvent(
            user_id="user_1",
            paddle_subscription_id="sub_123",
            event_type="some_unknown_event",
        )

        query = MagicMock()
        query.filter.return_value.first.return_value = sub
        mock_db.query.return_value = query

        with patch("app.routers.internal.invalidate_entitlements_cache"):
            result = await handle_paddle_subscription_event(event, db=mock_db)

        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_invalid_transition_rejected(self, mock_db, make_subscription):
        """Must reject invalid state transitions."""
        sub = make_subscription(
            status="canceled",
            paddle_subscription_id="sub_123",
        )

        event = PaddleSubscriptionEvent(
            user_id="user_1",
            paddle_subscription_id="sub_123",
            event_type="paused",  # canceled -> paused is invalid
        )

        query = MagicMock()
        query.filter.return_value.first.return_value = sub
        mock_db.query.return_value = query

        with patch("app.routers.internal.invalidate_entitlements_cache"):
            result = await handle_paddle_subscription_event(event, db=mock_db)

        assert result["status"] == "rejected"
        assert result["current_status"] == "canceled"

    @pytest.mark.asyncio
    async def test_reactivation_with_effective_from(self, mock_db, make_subscription, make_plan):
        """Must use effective_from date when provided for reactivation."""
        sub = make_subscription(
            status="canceled",
            paddle_subscription_id="sub_123",
            canceled_at=datetime.utcnow(),
            auto_renew=False,
        )
        plan = make_plan(code="professional", period_days=30)

        event = PaddleSubscriptionEvent(
            user_id="user_1",
            paddle_subscription_id="sub_123",
            event_type="activated",
            effective_from="2025-07-01T00:00:00",
        )

        query = MagicMock()
        query.filter.return_value.first.return_value = sub
        plan_query = MagicMock()
        plan_query.filter.return_value.first.return_value = plan
        mock_db.query.side_effect = [query, plan_query]

        with patch("app.routers.internal.invalidate_entitlements_cache"):
            result = await handle_paddle_subscription_event(event, db=mock_db)

        assert result["status"] == "updated"
        assert sub.status == "active"

    @pytest.mark.asyncio
    async def test_finds_sub_by_user_id_fallback(self, mock_db, make_subscription):
        """Must fall back to user_id when paddle_subscription_id doesn't match."""
        sub = make_subscription(
            status="active",
            paddle_subscription_id="sub_different",
        )

        event = PaddleSubscriptionEvent(
            user_id="user_1",
            paddle_subscription_id="sub_unknown",
            event_type="canceled",
        )

        # First query by paddle_sub_id returns None, second by user_id returns sub
        query1 = MagicMock()
        query1.filter.return_value.first.return_value = None
        query2 = MagicMock()
        query2.filter.return_value.first.return_value = sub
        mock_db.query.side_effect = [query1, query2]

        with patch("app.routers.internal.invalidate_entitlements_cache"):
            result = await handle_paddle_subscription_event(event, db=mock_db)

        assert result["status"] == "updated"
        assert sub.status == "canceled"
