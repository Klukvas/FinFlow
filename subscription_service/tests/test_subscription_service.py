"""Tests for SubscriptionService business logic."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.subscriptions import SubscriptionService
from app.utils.errors import ValidationError, NotFoundError


class TestSetPlan:
    """Tests for SubscriptionService.set_plan."""

    def _build_service(self, mock_db):
        """Build service with patched dependencies."""
        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            event_bus = MagicMock()
            MockEventBus.return_value = event_bus
            service = SubscriptionService(mock_db)
            service.events = event_bus
        return service

    def test_set_plan_creates_new_subscription(self, mock_db, make_plan, make_subscription):
        """set_plan must create a subscription when user has none."""
        plan = make_plan(code="professional")
        sub = make_subscription(plan_code="professional")

        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            MockEventBus.return_value = MagicMock()
            service = SubscriptionService(mock_db)
            service.plans.get_by_code = MagicMock(return_value=plan)
            service.repo.get_active_subscription = MagicMock(return_value=None)
            service.repo.upsert_subscription = MagicMock(return_value=sub)
            service.repo.get_entitlements = MagicMock(return_value=(1, {}))

            result = service.set_plan("user_1", "professional")

        assert result["subscription"] == sub
        assert result["is_downgrade"] is False
        assert result["downgrade_impact"] == []
        service.repo.upsert_subscription.assert_called_once_with("user_1", "professional", None)

    def test_set_plan_inactive_plan_raises_not_found(self, mock_db, make_plan):
        """set_plan must raise NotFoundError for inactive plan."""
        plan = make_plan(is_active=False)

        with (
            patch("app.services.subscriptions.EventBus"),
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            service = SubscriptionService(mock_db)
            service.plans.get_by_code = MagicMock(return_value=plan)

            with pytest.raises(NotFoundError, match="Plan not found"):
                service.set_plan("user_1", "professional")

    def test_set_plan_nonexistent_plan_raises_not_found(self, mock_db):
        """set_plan must raise NotFoundError when plan does not exist."""
        with (
            patch("app.services.subscriptions.EventBus"),
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            service = SubscriptionService(mock_db)
            service.plans.get_by_code = MagicMock(return_value=None)

            with pytest.raises(NotFoundError, match="Plan not found"):
                service.set_plan("user_1", "nonexistent")

    def test_set_plan_invalid_status_raises_validation_error(self, mock_db, make_plan):
        """set_plan must reject invalid status values."""
        plan = make_plan(code="professional")

        with (
            patch("app.services.subscriptions.EventBus"),
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            service = SubscriptionService(mock_db)
            service.plans.get_by_code = MagicMock(return_value=plan)

            with pytest.raises(ValidationError, match="Invalid status"):
                service.set_plan("user_1", "professional", status="invalid_status")

    def test_set_plan_valid_status_accepted(self, mock_db, make_plan, make_subscription):
        """set_plan must accept valid status values."""
        plan = make_plan(code="professional")
        sub = make_subscription(plan_code="professional", status="paused")

        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            MockEventBus.return_value = MagicMock()
            service = SubscriptionService(mock_db)
            service.plans.get_by_code = MagicMock(return_value=plan)
            service.repo.get_active_subscription = MagicMock(return_value=None)
            service.repo.upsert_subscription = MagicMock(return_value=sub)
            service.repo.get_entitlements = MagicMock(return_value=(1, {}))

            for valid_status in ("active", "past_due", "canceled", "paused"):
                result = service.set_plan("user_1", "professional", status=valid_status)
                assert result["subscription"] is not None

    def test_set_plan_publishes_event(self, mock_db, make_plan, make_subscription):
        """set_plan must publish a subscription.changed event."""
        plan = make_plan(code="professional")
        sub = make_subscription(plan_code="professional")

        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            event_bus = MagicMock()
            MockEventBus.return_value = event_bus
            service = SubscriptionService(mock_db)
            service.plans.get_by_code = MagicMock(return_value=plan)
            service.repo.get_active_subscription = MagicMock(return_value=None)
            service.repo.upsert_subscription = MagicMock(return_value=sub)
            service.repo.get_entitlements = MagicMock(return_value=(2, {"accounts": {"enabled": True, "limit_value": 5}}))

            service.set_plan("user_1", "professional")

        event_bus.publish_subscription_changed.assert_called_once()
        call_kwargs = event_bus.publish_subscription_changed.call_args[1]
        assert call_kwargs["user_id"] == "user_1"
        assert call_kwargs["plan_code"] == "professional"
        assert call_kwargs["version"] == 2

    def test_set_plan_invalidates_entitlements_cache(self, mock_db, make_plan, make_subscription):
        """set_plan must invalidate entitlements cache."""
        plan = make_plan(code="professional")
        sub = make_subscription(plan_code="professional")

        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache") as mock_invalidate,
        ):
            MockEventBus.return_value = MagicMock()
            service = SubscriptionService(mock_db)
            service.plans.get_by_code = MagicMock(return_value=plan)
            service.repo.get_active_subscription = MagicMock(return_value=None)
            service.repo.upsert_subscription = MagicMock(return_value=sub)
            service.repo.get_entitlements = MagicMock(return_value=(1, {}))

            service.set_plan("user_1", "professional")

        mock_invalidate.assert_called_once_with("user_1")


class TestComputeDowngradeImpact:
    """Tests for SubscriptionService._compute_downgrade_impact."""

    def _build_service(self, mock_db):
        with (
            patch("app.services.subscriptions.EventBus"),
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            return SubscriptionService(mock_db)

    def test_no_impact_when_same_features(self, mock_db):
        """No downgrade impact when both plans have identical features."""
        service = self._build_service(mock_db)
        old_ents = {"accounts": {"enabled": True, "limit_value": 5}}
        new_ents = {"accounts": {"enabled": True, "limit_value": 5}}
        service.repo.get_entitlements = MagicMock(side_effect=[
            (1, old_ents), (1, new_ents),
        ])

        result = service._compute_downgrade_impact("user_1", "pro", "pro")
        assert result == []

    def test_detects_reduced_limit(self, mock_db):
        """Must detect when a feature limit is reduced."""
        service = self._build_service(mock_db)
        old_ents = {"accounts": {"enabled": True, "limit_value": 10}}
        new_ents = {"accounts": {"enabled": True, "limit_value": 3}}
        service.repo.get_entitlements = MagicMock(side_effect=[
            (1, old_ents), (1, new_ents),
        ])

        result = service._compute_downgrade_impact("user_1", "pro", "basic")
        assert len(result) == 1
        assert result[0]["feature"] == "accounts"
        assert result[0]["change"] == "reduced"
        assert result[0]["old_limit"] == 10
        assert result[0]["new_limit"] == 3

    def test_detects_disabled_feature(self, mock_db):
        """Must detect when a feature is disabled."""
        service = self._build_service(mock_db)
        old_ents = {"ai_assistant": {"enabled": True, "limit_value": 100}}
        new_ents = {"ai_assistant": {"enabled": False, "limit_value": 0}}
        service.repo.get_entitlements = MagicMock(side_effect=[
            (1, old_ents), (1, new_ents),
        ])

        result = service._compute_downgrade_impact("user_1", "pro", "basic")
        assert len(result) == 1
        assert result[0]["change"] == "disabled"

    def test_detects_removed_feature(self, mock_db):
        """Must detect when a feature is completely removed."""
        service = self._build_service(mock_db)
        old_ents = {"ai_assistant": {"enabled": True, "limit_value": 100}}
        new_ents = {}
        service.repo.get_entitlements = MagicMock(side_effect=[
            (1, old_ents), (1, new_ents),
        ])

        result = service._compute_downgrade_impact("user_1", "pro", "basic")
        assert len(result) == 1
        assert result[0]["change"] == "removed"
        assert result[0]["new_limit"] is None

    def test_no_impact_when_feature_disabled_in_both(self, mock_db):
        """No impact reported for features disabled in old plan too."""
        service = self._build_service(mock_db)
        old_ents = {"pdf": {"enabled": False, "limit_value": 0}}
        new_ents = {}
        service.repo.get_entitlements = MagicMock(side_effect=[
            (1, old_ents), (1, new_ents),
        ])

        result = service._compute_downgrade_impact("user_1", "pro", "basic")
        assert result == []

    def test_returns_empty_when_plan_not_found(self, mock_db):
        """Must return empty list when plan lookup fails."""
        service = self._build_service(mock_db)
        service.repo.get_entitlements = MagicMock(side_effect=ValueError("PLAN_NOT_FOUND"))

        result = service._compute_downgrade_impact("user_1", "bad_plan", "basic")
        assert result == []

    def test_set_plan_detects_downgrade(self, mock_db, make_plan, make_subscription):
        """set_plan must detect and report downgrade impact."""
        plan = make_plan(code="basic")
        old_sub = make_subscription(plan_code="professional")
        new_sub = make_subscription(plan_code="basic")

        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            MockEventBus.return_value = MagicMock()
            service = SubscriptionService(mock_db)
            service.plans.get_by_code = MagicMock(return_value=plan)
            service.repo.get_active_subscription = MagicMock(return_value=old_sub)
            service.repo.upsert_subscription = MagicMock(return_value=new_sub)

            old_ents = {"accounts": {"enabled": True, "limit_value": 20}}
            new_ents = {"accounts": {"enabled": True, "limit_value": 3}}
            service.repo.get_entitlements = MagicMock(side_effect=[
                (1, old_ents), (1, new_ents), (1, new_ents),
            ])

            result = service.set_plan("user_1", "basic")

        assert result["is_downgrade"] is True
        assert len(result["downgrade_impact"]) == 1


class TestCancelSubscription:
    """Tests for SubscriptionService.cancel_subscription."""

    def _build_service(self, mock_db):
        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            event_bus = MagicMock()
            MockEventBus.return_value = event_bus
            service = SubscriptionService(mock_db)
            service.events = event_bus
        return service

    def test_cancel_at_period_end(self, mock_db, make_subscription):
        """Cancel at period end keeps status active but sets auto_renew=False."""
        sub = make_subscription(status="active", auto_renew=True)
        mock_db.query.return_value.filter_by.return_value.first.return_value = sub

        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            MockEventBus.return_value = MagicMock()
            service = SubscriptionService(mock_db)

            result = service.cancel_subscription(
                user_id="user_1",
                cancellation_reason="too_expensive",
                cancellation_comment="I found cheaper",
                cancel_immediately=False,
                ip_address="192.168.1.1",
            )

        assert sub.auto_renew is False
        assert sub.cancellation_reason == "too_expensive"
        assert sub.cancellation_comment == "I found cheaper"
        assert sub.cancellation_ip_address == "192.168.1.1"
        assert sub.canceled_at is not None
        # Status stays active for period-end cancellation
        assert sub.status == "active"
        mock_db.commit.assert_called_once()

    def test_cancel_immediately(self, mock_db, make_subscription):
        """Immediate cancellation sets status to canceled and expires access."""
        sub = make_subscription(status="active", auto_renew=True)
        mock_db.query.return_value.filter_by.return_value.first.return_value = sub

        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            event_bus = MagicMock()
            MockEventBus.return_value = event_bus
            service = SubscriptionService(mock_db)
            service.events = event_bus
            service.repo.get_entitlements = MagicMock(return_value=(1, {}))

            result = service.cancel_subscription(
                user_id="user_1",
                cancellation_reason="not_using",
                cancellation_comment=None,
                cancel_immediately=True,
                ip_address="10.0.0.1",
            )

        assert sub.status == "canceled"
        assert sub.auto_renew is False
        event_bus.publish_subscription_changed.assert_called_once()

    def test_cancel_no_subscription_raises_not_found(self, mock_db):
        """Must raise NotFoundError when user has no subscription."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with (
            patch("app.services.subscriptions.EventBus"),
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            service = SubscriptionService(mock_db)

            with pytest.raises(NotFoundError, match="No subscription found"):
                service.cancel_subscription(
                    user_id="user_no_sub",
                    cancellation_reason=None,
                    cancellation_comment=None,
                    cancel_immediately=False,
                    ip_address="10.0.0.1",
                )

    def test_cancel_already_canceled_raises_validation_error(self, mock_db, make_subscription):
        """Must raise ValidationError when subscription is already canceled."""
        sub = make_subscription(status="canceled", auto_renew=False)
        mock_db.query.return_value.filter_by.return_value.first.return_value = sub

        with (
            patch("app.services.subscriptions.EventBus"),
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            service = SubscriptionService(mock_db)

            with pytest.raises(ValidationError, match="already canceled"):
                service.cancel_subscription(
                    user_id="user_1",
                    cancellation_reason=None,
                    cancellation_comment=None,
                    cancel_immediately=False,
                    ip_address="10.0.0.1",
                )

    def test_cancel_immediately_from_canceled_is_noop(self, mock_db, make_subscription):
        """Immediately canceling an already-canceled subscription is a no-op.

        The state machine treats canceled -> canceled as a same-status
        transition (always allowed), so no error is raised.
        """
        sub = make_subscription(status="canceled", auto_renew=False)
        mock_db.query.return_value.filter_by.return_value.first.return_value = sub

        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            MockEventBus.return_value = MagicMock()
            service = SubscriptionService(mock_db)
            service.events = MockEventBus.return_value
            service.repo.get_entitlements = MagicMock(return_value=(1, {}))

            result = service.cancel_subscription(
                user_id="user_1",
                cancellation_reason=None,
                cancellation_comment=None,
                cancel_immediately=True,
                ip_address="10.0.0.1",
            )

        # No error raised, subscription stays canceled
        assert sub.status == "canceled"

    def test_cancel_invalidates_cache(self, mock_db, make_subscription):
        """Cancel must invalidate entitlements cache."""
        sub = make_subscription(status="active", auto_renew=True)
        mock_db.query.return_value.filter_by.return_value.first.return_value = sub

        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache") as mock_invalidate,
        ):
            MockEventBus.return_value = MagicMock()
            service = SubscriptionService(mock_db)

            service.cancel_subscription(
                user_id="user_1",
                cancellation_reason=None,
                cancellation_comment=None,
                cancel_immediately=False,
                ip_address="10.0.0.1",
            )

        mock_invalidate.assert_called_once_with("user_1")

    def test_cancel_past_due_subscription_immediately(self, mock_db, make_subscription):
        """Must be able to immediately cancel a past_due subscription."""
        sub = make_subscription(status="past_due", auto_renew=True)
        mock_db.query.return_value.filter_by.return_value.first.return_value = sub

        with (
            patch("app.services.subscriptions.EventBus") as MockEventBus,
            patch("app.services.subscriptions.invalidate_entitlements_cache"),
        ):
            MockEventBus.return_value = MagicMock()
            service = SubscriptionService(mock_db)
            service.events = MockEventBus.return_value
            service.repo.get_entitlements = MagicMock(return_value=(1, {}))

            result = service.cancel_subscription(
                user_id="user_1",
                cancellation_reason="not_using",
                cancellation_comment=None,
                cancel_immediately=True,
                ip_address="10.0.0.1",
            )

        assert sub.status == "canceled"
        assert sub.auto_renew is False
