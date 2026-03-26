"""Tests for subscriptions router endpoints."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.routers.subscriptions import (
    get_subscription,
    set_plan,
    cancel_subscription,
    cancel_subscription_legacy,
)
from app.schemas.subscription import SetPlanIn
from app.schemas.cancellation import CancelSubscriptionRequest
from app.utils.errors import NotFoundError, ConflictError

_SENTINEL = object()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sub(
    id: int = 1,
    user_id: str = "user_1",
    plan_code: str = "professional",
    status: str = "active",
    auto_renew: bool = True,
    expires_at: datetime | None | object = _SENTINEL,
    canceled_at: datetime | None = None,
    cancellation_reason: str | None = None,
):
    sub = MagicMock()
    sub.id = id
    sub.user_id = user_id
    sub.plan_code = plan_code
    sub.status = status
    sub.auto_renew = auto_renew
    sub.started_at = datetime.utcnow()
    sub.expires_at = (datetime.utcnow() + timedelta(days=30)) if expires_at is _SENTINEL else expires_at
    sub.canceled_at = canceled_at
    sub.cancellation_reason = cancellation_reason
    sub.recurring_token = None
    sub.next_billing_date = None
    sub.paddle_customer_id = None
    sub.paddle_subscription_id = None
    sub.paddle_price_id = None
    sub.cancellation_comment = None
    sub.created_at = datetime.utcnow()
    sub.updated_at = datetime.utcnow()
    return sub


def _make_http_request(host: str = "192.168.1.1"):
    request = MagicMock()
    client = MagicMock()
    client.host = host
    request.client = client
    return request


# ---------------------------------------------------------------------------
# get_subscription
# ---------------------------------------------------------------------------


class TestGetSubscription:
    """Tests for GET /subscriptions/{user_id}."""

    @patch("app.routers.subscriptions.SubscriptionRepository")
    def test_returns_subscription(self, MockSubRepo, mock_db):
        sub = _make_sub()
        mock_repo = MagicMock()
        mock_repo.get_active_subscription.return_value = sub
        MockSubRepo.return_value = mock_repo

        with patch("app.routers.subscriptions.SubscriptionOut") as MockOut:
            MockOut.model_validate.return_value = MagicMock(
                user_id="user_1", plan_code="professional"
            )
            result = get_subscription(user_id="user_1", db=mock_db)

        assert result.user_id == "user_1"
        mock_repo.get_active_subscription.assert_called_once_with("user_1")

    @patch("app.routers.subscriptions.SubscriptionRepository")
    def test_returns_none_when_no_subscription(self, MockSubRepo, mock_db):
        """Must return None (200) when no active subscription exists."""
        mock_repo = MagicMock()
        mock_repo.get_active_subscription.return_value = None
        MockSubRepo.return_value = mock_repo

        result = get_subscription(user_id="user_unknown", db=mock_db)

        assert result is None
        mock_repo.get_active_subscription.assert_called_once_with("user_unknown")


# ---------------------------------------------------------------------------
# set_plan
# ---------------------------------------------------------------------------


class TestSetPlan:
    """Tests for POST /subscriptions/{user_id}:set_plan."""

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_sets_plan_successfully(self, MockSubService, mock_db):
        sub = _make_sub(plan_code="basic")

        mock_service = MagicMock()
        mock_service.set_plan.return_value = {
            "subscription": sub,
            "downgrade_impact": [],
            "is_downgrade": False,
        }
        MockSubService.return_value = mock_service

        payload = SetPlanIn(plan_code="basic")

        with patch("app.routers.subscriptions.SubscriptionOut") as MockOut:
            mock_out = MagicMock()
            mock_out.model_dump.return_value = {"user_id": "user_1", "plan_code": "basic"}
            MockOut.model_validate.return_value = mock_out

            result = set_plan(
                user_id="user_1",
                payload=payload,
                db=mock_db,
                _=None,
                idempotency_key=None,
            )

        assert "user_id" in result
        mock_service.set_plan.assert_called_once_with("user_1", "basic", None)

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_downgrade_includes_impact(self, MockSubService, mock_db):
        sub = _make_sub(plan_code="basic")

        mock_service = MagicMock()
        mock_service.set_plan.return_value = {
            "subscription": sub,
            "downgrade_impact": [
                {"feature": "accounts", "old_limit": 20, "new_limit": 5, "change": "reduced"}
            ],
            "is_downgrade": True,
        }
        MockSubService.return_value = mock_service

        payload = SetPlanIn(plan_code="basic")

        with patch("app.routers.subscriptions.SubscriptionOut") as MockOut:
            mock_out = MagicMock()
            mock_out.model_dump.return_value = {"user_id": "user_1", "plan_code": "basic"}
            MockOut.model_validate.return_value = mock_out

            result = set_plan(
                user_id="user_1",
                payload=payload,
                db=mock_db,
                _=None,
                idempotency_key=None,
            )

        assert result["is_downgrade"] is True
        assert len(result["downgrade_impact"]) == 1

    @patch("app.routers.subscriptions.IdempotencyStore")
    @patch("app.routers.subscriptions.SubscriptionService")
    def test_idempotency_conflict_raises(self, MockSubService, MockIdempStore, mock_db):
        mock_store = MagicMock()
        mock_store.check_and_set.return_value = False
        MockIdempStore.return_value = mock_store

        payload = SetPlanIn(plan_code="professional")

        with pytest.raises(ConflictError):
            set_plan(
                user_id="user_1",
                payload=payload,
                db=mock_db,
                _=None,
                idempotency_key="key_123",
            )

    @patch("app.routers.subscriptions.IdempotencyStore")
    @patch("app.routers.subscriptions.SubscriptionService")
    def test_idempotency_ok_proceeds(self, MockSubService, MockIdempStore, mock_db):
        mock_store = MagicMock()
        mock_store.check_and_set.return_value = True
        MockIdempStore.return_value = mock_store

        sub = _make_sub(plan_code="professional")
        mock_service = MagicMock()
        mock_service.set_plan.return_value = {
            "subscription": sub,
            "downgrade_impact": [],
            "is_downgrade": False,
        }
        MockSubService.return_value = mock_service

        payload = SetPlanIn(plan_code="professional")

        with patch("app.routers.subscriptions.SubscriptionOut") as MockOut:
            mock_out = MagicMock()
            mock_out.model_dump.return_value = {"plan_code": "professional"}
            MockOut.model_validate.return_value = mock_out

            result = set_plan(
                user_id="user_1",
                payload=payload,
                db=mock_db,
                _=None,
                idempotency_key="key_456",
            )

        assert "plan_code" in result

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_no_idempotency_key_skips_check(self, MockSubService, mock_db):
        sub = _make_sub()
        mock_service = MagicMock()
        mock_service.set_plan.return_value = {
            "subscription": sub,
            "downgrade_impact": [],
            "is_downgrade": False,
        }
        MockSubService.return_value = mock_service

        payload = SetPlanIn(plan_code="professional")

        with patch("app.routers.subscriptions.SubscriptionOut") as MockOut:
            mock_out = MagicMock()
            mock_out.model_dump.return_value = {}
            MockOut.model_validate.return_value = mock_out

            # Should not raise; idempotency check skipped
            set_plan(
                user_id="user_1",
                payload=payload,
                db=mock_db,
                _=None,
                idempotency_key=None,
            )

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_set_plan_with_status_override(self, MockSubService, mock_db):
        sub = _make_sub(status="paused")
        mock_service = MagicMock()
        mock_service.set_plan.return_value = {
            "subscription": sub,
            "downgrade_impact": [],
            "is_downgrade": False,
        }
        MockSubService.return_value = mock_service

        payload = SetPlanIn(plan_code="professional", status="paused")

        with patch("app.routers.subscriptions.SubscriptionOut") as MockOut:
            mock_out = MagicMock()
            mock_out.model_dump.return_value = {}
            MockOut.model_validate.return_value = mock_out

            set_plan(
                user_id="user_1",
                payload=payload,
                db=mock_db,
                _=None,
                idempotency_key=None,
            )

        mock_service.set_plan.assert_called_once_with("user_1", "professional", "paused")


# ---------------------------------------------------------------------------
# cancel_subscription
# ---------------------------------------------------------------------------


class TestCancelSubscription:
    """Tests for DELETE /subscriptions/{user_id}/cancel."""

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_cancel_at_period_end(self, MockSubService, mock_db):
        expires = datetime.utcnow() + timedelta(days=15)
        sub = _make_sub(
            status="active",
            auto_renew=False,
            canceled_at=datetime.utcnow(),
            expires_at=expires,
            cancellation_reason="too_expensive",
        )

        mock_service = MagicMock()
        mock_service.cancel_subscription.return_value = sub
        MockSubService.return_value = mock_service

        request_data = CancelSubscriptionRequest(
            cancellation_reason="too_expensive",
            cancel_immediately=False,
        )
        http_request = _make_http_request()

        result = cancel_subscription(
            user_id="user_1",
            request_data=request_data,
            http_request=http_request,
            db=mock_db,
        )

        assert result.auto_renew is False
        assert "access until" in result.message

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_cancel_immediately(self, MockSubService, mock_db):
        sub = _make_sub(
            status="canceled",
            auto_renew=False,
            canceled_at=datetime.utcnow(),
            expires_at=datetime.utcnow(),
        )

        mock_service = MagicMock()
        mock_service.cancel_subscription.return_value = sub
        MockSubService.return_value = mock_service

        request_data = CancelSubscriptionRequest(
            cancellation_reason="not_using",
            cancel_immediately=True,
        )
        http_request = _make_http_request()

        result = cancel_subscription(
            user_id="user_1",
            request_data=request_data,
            http_request=http_request,
            db=mock_db,
        )

        assert "canceled immediately" in result.message
        mock_service.cancel_subscription.assert_called_once_with(
            user_id="user_1",
            cancellation_reason="not_using",
            cancellation_comment=None,
            cancel_immediately=True,
            ip_address="192.168.1.1",
        )

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_extracts_ip_address(self, MockSubService, mock_db):
        sub = _make_sub()
        mock_service = MagicMock()
        mock_service.cancel_subscription.return_value = sub
        MockSubService.return_value = mock_service

        request_data = CancelSubscriptionRequest()
        http_request = _make_http_request(host="10.0.0.5")

        cancel_subscription(
            user_id="user_1",
            request_data=request_data,
            http_request=http_request,
            db=mock_db,
        )

        call_kwargs = mock_service.cancel_subscription.call_args.kwargs
        assert call_kwargs["ip_address"] == "10.0.0.5"

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_handles_missing_client(self, MockSubService, mock_db):
        sub = _make_sub()
        mock_service = MagicMock()
        mock_service.cancel_subscription.return_value = sub
        MockSubService.return_value = mock_service

        request_data = CancelSubscriptionRequest()
        http_request = MagicMock()
        http_request.client = None

        cancel_subscription(
            user_id="user_1",
            request_data=request_data,
            http_request=http_request,
            db=mock_db,
        )

        call_kwargs = mock_service.cancel_subscription.call_args.kwargs
        assert call_kwargs["ip_address"] == "unknown"

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_cancel_no_expires_at_message(self, MockSubService, mock_db):
        """Must produce correct message when expires_at is None."""
        sub = _make_sub(
            status="active",
            auto_renew=False,
            canceled_at=datetime.utcnow(),
            expires_at=None,
        )

        mock_service = MagicMock()
        mock_service.cancel_subscription.return_value = sub
        MockSubService.return_value = mock_service

        request_data = CancelSubscriptionRequest(cancel_immediately=False)
        http_request = _make_http_request()

        result = cancel_subscription(
            user_id="user_1",
            request_data=request_data,
            http_request=http_request,
            db=mock_db,
        )

        assert "No future charges" in result.message

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_passes_comment_to_service(self, MockSubService, mock_db):
        sub = _make_sub()
        mock_service = MagicMock()
        mock_service.cancel_subscription.return_value = sub
        MockSubService.return_value = mock_service

        request_data = CancelSubscriptionRequest(
            cancellation_reason="other",
            cancellation_comment="I found a better alternative",
        )
        http_request = _make_http_request()

        cancel_subscription(
            user_id="user_1",
            request_data=request_data,
            http_request=http_request,
            db=mock_db,
        )

        call_kwargs = mock_service.cancel_subscription.call_args.kwargs
        assert call_kwargs["cancellation_comment"] == "I found a better alternative"


# ---------------------------------------------------------------------------
# cancel_subscription_legacy
# ---------------------------------------------------------------------------


class TestCancelSubscriptionLegacy:
    """Tests for POST /subscriptions/{user_id}:cancel (deprecated)."""

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_cancels_at_period_end(self, MockSubService, mock_db):
        sub = _make_sub(auto_renew=False, canceled_at=datetime.utcnow())

        mock_service = MagicMock()
        mock_service.cancel_subscription.return_value = sub
        MockSubService.return_value = mock_service

        http_request = _make_http_request()

        with patch("app.routers.subscriptions.SubscriptionOut") as MockOut:
            MockOut.model_validate.return_value = MagicMock(
                user_id="user_1", auto_renew=False
            )
            result = cancel_subscription_legacy(
                user_id="user_1", http_request=http_request, db=mock_db
            )

        mock_service.cancel_subscription.assert_called_once_with(
            user_id="user_1",
            cancellation_reason=None,
            cancellation_comment=None,
            cancel_immediately=False,
            ip_address="192.168.1.1",
        )

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_legacy_uses_ip_from_request(self, MockSubService, mock_db):
        sub = _make_sub()
        mock_service = MagicMock()
        mock_service.cancel_subscription.return_value = sub
        MockSubService.return_value = mock_service

        http_request = _make_http_request(host="172.16.0.1")

        with patch("app.routers.subscriptions.SubscriptionOut") as MockOut:
            MockOut.model_validate.return_value = MagicMock()
            cancel_subscription_legacy(
                user_id="user_1", http_request=http_request, db=mock_db
            )

        call_kwargs = mock_service.cancel_subscription.call_args.kwargs
        assert call_kwargs["ip_address"] == "172.16.0.1"

    @patch("app.routers.subscriptions.SubscriptionService")
    def test_legacy_handles_missing_client(self, MockSubService, mock_db):
        sub = _make_sub()
        mock_service = MagicMock()
        mock_service.cancel_subscription.return_value = sub
        MockSubService.return_value = mock_service

        http_request = MagicMock()
        http_request.client = None

        with patch("app.routers.subscriptions.SubscriptionOut") as MockOut:
            MockOut.model_validate.return_value = MagicMock()
            cancel_subscription_legacy(
                user_id="user_1", http_request=http_request, db=mock_db
            )

        call_kwargs = mock_service.cancel_subscription.call_args.kwargs
        assert call_kwargs["ip_address"] == "unknown"
