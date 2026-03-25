"""Tests for the reconciliation service.

Tests reconcile_payments, _check_subscription_for_payment,
_handle_mismatch, _fetch_paid_payments, and check_stale_paddle_subscriptions.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

import httpx

from payment_service.app.services.reconciliation import (
    reconcile_payments,
    _check_subscription_for_payment,
    _handle_mismatch,
    _fetch_paid_payments,
    check_stale_paddle_subscriptions,
)


# ======================================================================
# _check_subscription_for_payment
# ======================================================================


class TestCheckSubscriptionForPayment:
    """Tests for _check_subscription_for_payment."""

    @pytest.mark.asyncio
    async def test_returns_none_when_subscription_healthy(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"status": "active", "plan_code": "pro"}
        mock_client.get = AsyncMock(return_value=mock_response)

        payment_dict = {
            "id": uuid4(),
            "user_id": "user_1",
            "plan_code": "pro",
        }

        result = await _check_subscription_for_payment(mock_client, payment_dict)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_mismatch_when_no_subscription(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.is_success = False
        mock_client.get = AsyncMock(return_value=mock_response)

        payment_dict = {
            "id": uuid4(),
            "user_id": "user_orphan",
            "plan_code": "pro",
        }

        result = await _check_subscription_for_payment(mock_client, payment_dict)
        assert result == "no_active_subscription"

    @pytest.mark.asyncio
    async def test_returns_mismatch_when_unexpected_status(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"status": "canceled", "plan_code": "pro"}
        mock_client.get = AsyncMock(return_value=mock_response)

        payment_dict = {
            "id": uuid4(),
            "user_id": "user_1",
            "plan_code": "pro",
        }

        result = await _check_subscription_for_payment(mock_client, payment_dict)
        assert "unexpected_status" in result

    @pytest.mark.asyncio
    async def test_returns_mismatch_when_plan_differs(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"status": "active", "plan_code": "enterprise"}
        mock_client.get = AsyncMock(return_value=mock_response)

        payment_dict = {
            "id": uuid4(),
            "user_id": "user_1",
            "plan_code": "professional",
        }

        result = await _check_subscription_for_payment(mock_client, payment_dict)
        assert "plan_mismatch" in result

    @pytest.mark.asyncio
    async def test_returns_none_on_5xx_error(self):
        """Server errors should not be treated as mismatches."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.is_success = False
        mock_client.get = AsyncMock(return_value=mock_response)

        payment_dict = {
            "id": uuid4(),
            "user_id": "user_1",
            "plan_code": "pro",
        }

        result = await _check_subscription_for_payment(mock_client, payment_dict)
        assert result is None

    @pytest.mark.asyncio
    async def test_past_due_status_is_healthy(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"status": "past_due", "plan_code": "pro"}
        mock_client.get = AsyncMock(return_value=mock_response)

        payment_dict = {"id": uuid4(), "user_id": "u1", "plan_code": "pro"}

        result = await _check_subscription_for_payment(mock_client, payment_dict)
        assert result is None

    @pytest.mark.asyncio
    async def test_paused_status_is_healthy(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"status": "paused", "plan_code": "pro"}
        mock_client.get = AsyncMock(return_value=mock_response)

        payment_dict = {"id": uuid4(), "user_id": "u1", "plan_code": "pro"}

        result = await _check_subscription_for_payment(mock_client, payment_dict)
        assert result is None


# ======================================================================
# _handle_mismatch
# ======================================================================


class TestHandleMismatch:
    """Tests for _handle_mismatch."""

    @patch("payment_service.app.services.reconciliation.SessionLocal")
    @patch("payment_service.app.services.reconciliation.settings")
    def test_inserts_outbox_event_and_returns_true(self, mock_settings, mock_session_local):
        mock_settings.subscription_service_url = "http://sub-service"
        mock_settings.internal_secret_token = "token"

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result
        mock_session_local.return_value = mock_db

        payment_dict = {
            "id": uuid4(),
            "user_id": "user_mismatch",
            "workspace_id": "ws_1",
            "plan_code": "pro",
            "amount": "29.99",
            "currency": "USD",
        }

        result = _handle_mismatch(payment_dict, "no_active_subscription")

        assert result is True
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("payment_service.app.services.reconciliation.SessionLocal")
    @patch("payment_service.app.services.reconciliation.settings")
    def test_returns_false_when_event_already_exists(self, mock_settings, mock_session_local):
        mock_settings.subscription_service_url = "http://sub-service"
        mock_settings.internal_secret_token = "token"

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0  # ON CONFLICT DO NOTHING
        mock_db.execute.return_value = mock_result
        mock_session_local.return_value = mock_db

        payment_dict = {
            "id": uuid4(),
            "user_id": "user_dup",
            "workspace_id": None,
            "plan_code": "pro",
            "amount": "10.00",
            "currency": "USD",
        }

        result = _handle_mismatch(payment_dict, "plan_mismatch:pro!=ent")
        assert result is False


# ======================================================================
# reconcile_payments
# ======================================================================


class TestReconcilePayments:
    """Tests for reconcile_payments."""

    @pytest.mark.asyncio
    @patch("payment_service.app.services.reconciliation._fetch_paid_payments")
    @patch("payment_service.app.services.reconciliation.asyncio")
    async def test_returns_empty_stats_when_no_payments(self, mock_asyncio, mock_fetch):
        mock_asyncio.to_thread = AsyncMock(return_value=[])

        stats = await reconcile_payments()

        assert stats["checked"] == 0
        assert stats["mismatches"] == 0
        assert stats["requeued"] == 0
        assert stats["errors"] == 0

    @pytest.mark.asyncio
    @patch("payment_service.app.services.reconciliation._handle_mismatch")
    @patch("payment_service.app.services.reconciliation._check_subscription_for_payment")
    @patch("payment_service.app.services.reconciliation.asyncio")
    async def test_detects_and_requeues_mismatches(self, mock_asyncio, mock_check, mock_handle):
        payment_dicts = [
            {"id": uuid4(), "user_id": "u1", "plan_code": "pro",
             "workspace_id": None, "amount": "10", "currency": "USD"},
        ]
        mock_asyncio.to_thread = AsyncMock(side_effect=[payment_dicts, True])
        mock_check.return_value = "no_active_subscription"

        stats = await reconcile_payments()

        assert stats["checked"] == 1
        assert stats["mismatches"] == 1

    @pytest.mark.asyncio
    @patch("payment_service.app.services.reconciliation._check_subscription_for_payment")
    @patch("payment_service.app.services.reconciliation.asyncio")
    async def test_counts_errors_on_exception(self, mock_asyncio, mock_check):
        payment_dicts = [
            {"id": uuid4(), "user_id": "u1", "plan_code": "pro",
             "workspace_id": None, "amount": "10", "currency": "USD"},
        ]
        mock_asyncio.to_thread = AsyncMock(return_value=payment_dicts)
        mock_check.side_effect = Exception("network error")

        stats = await reconcile_payments()

        assert stats["errors"] == 1
        assert stats["checked"] == 1

    @pytest.mark.asyncio
    @patch("payment_service.app.services.reconciliation._check_subscription_for_payment")
    @patch("payment_service.app.services.reconciliation.asyncio")
    async def test_no_mismatch_when_subscription_healthy(self, mock_asyncio, mock_check):
        payment_dicts = [
            {"id": uuid4(), "user_id": "u1", "plan_code": "pro",
             "workspace_id": None, "amount": "10", "currency": "USD"},
        ]
        mock_asyncio.to_thread = AsyncMock(return_value=payment_dicts)
        mock_check.return_value = None  # Healthy

        stats = await reconcile_payments()

        assert stats["checked"] == 1
        assert stats["mismatches"] == 0


# ======================================================================
# _fetch_paid_payments
# ======================================================================


class TestFetchPaidPayments:
    """Tests for _fetch_paid_payments."""

    @patch("payment_service.app.services.reconciliation.SessionLocal")
    @patch("payment_service.app.services.reconciliation.settings")
    def test_returns_list_of_dicts(self, mock_settings, mock_session_local):
        mock_settings.reconciliation_lookback_hours = 24

        mock_payment = MagicMock()
        mock_payment.id = uuid4()
        mock_payment.user_id = "u1"
        mock_payment.workspace_id = "ws_1"
        mock_payment.plan_code = "pro"
        mock_payment.amount = 29.99
        mock_payment.currency = "USD"

        mock_db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_payment]
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        result = _fetch_paid_payments()

        assert len(result) == 1
        assert result[0]["user_id"] == "u1"
        assert result[0]["plan_code"] == "pro"
        mock_db.close.assert_called_once()

    @patch("payment_service.app.services.reconciliation.SessionLocal")
    @patch("payment_service.app.services.reconciliation.settings")
    def test_returns_empty_list_when_no_payments(self, mock_settings, mock_session_local):
        mock_settings.reconciliation_lookback_hours = 24

        mock_db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        result = _fetch_paid_payments()
        assert result == []


# ======================================================================
# check_stale_paddle_subscriptions
# ======================================================================


class TestCheckStalePaddleSubscriptions:
    """Tests for check_stale_paddle_subscriptions."""

    @pytest.mark.asyncio
    @patch("payment_service.app.services.reconciliation.settings")
    async def test_skips_when_no_paddle_api_key(self, mock_settings):
        mock_settings.paddle_api_key = ""

        stats = await check_stale_paddle_subscriptions()

        assert stats["checked"] == 0
        assert stats["renewed"] == 0
        assert stats["errors"] == 0

    @pytest.mark.asyncio
    @patch("payment_service.app.clients.paddle_client.PaddleClient")
    @patch("payment_service.app.services.reconciliation.settings")
    @patch("httpx.AsyncClient")
    async def test_returns_empty_stats_when_no_stale_subs(self, mock_async_client, mock_settings, mock_paddle_cls):
        mock_settings.paddle_api_key = "test_key"
        mock_settings.subscription_service_url = "http://sub-service"
        mock_settings.internal_secret_token = "token"

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.json.return_value = []  # No stale subscriptions

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client.return_value.__aexit__ = AsyncMock(return_value=False)

        stats = await check_stale_paddle_subscriptions()
        assert stats["checked"] == 0

    @pytest.mark.asyncio
    @patch("payment_service.app.clients.paddle_client.PaddleClient")
    @patch("payment_service.app.services.reconciliation.settings")
    @patch("httpx.AsyncClient")
    async def test_renews_active_paddle_subscription(self, mock_async_client, mock_settings, mock_paddle_cls):
        mock_settings.paddle_api_key = "test_key"
        mock_settings.subscription_service_url = "http://sub-service"
        mock_settings.internal_secret_token = "token"

        stale_subs = [
            {"id": 1, "user_id": "u1", "paddle_subscription_id": "sub_stale_1"},
        ]

        # First GET: fetch stale subs
        stale_response = MagicMock()
        stale_response.is_success = True
        stale_response.json.return_value = stale_subs

        # POST to forward event
        event_response = MagicMock()
        event_response.is_success = True

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=stale_response)
        mock_client_instance.post = AsyncMock(return_value=event_response)
        mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client.return_value.__aexit__ = AsyncMock(return_value=False)

        # PaddleClient says subscription is active
        mock_paddle = MagicMock()
        mock_paddle.get_subscription = AsyncMock(return_value={"status": "active"})
        mock_paddle_cls.return_value = mock_paddle

        stats = await check_stale_paddle_subscriptions()
        assert stats["checked"] == 1
        assert stats["renewed"] == 1

    @pytest.mark.asyncio
    @patch("payment_service.app.clients.paddle_client.PaddleClient")
    @patch("payment_service.app.services.reconciliation.settings")
    @patch("httpx.AsyncClient")
    async def test_does_not_renew_inactive_subscription(self, mock_async_client, mock_settings, mock_paddle_cls):
        mock_settings.paddle_api_key = "test_key"
        mock_settings.subscription_service_url = "http://sub-service"
        mock_settings.internal_secret_token = "token"

        stale_subs = [
            {"id": 1, "user_id": "u1", "paddle_subscription_id": "sub_canceled"},
        ]

        stale_response = MagicMock()
        stale_response.is_success = True
        stale_response.json.return_value = stale_subs

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=stale_response)
        mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_paddle = MagicMock()
        mock_paddle.get_subscription = AsyncMock(return_value={"status": "canceled"})
        mock_paddle_cls.return_value = mock_paddle

        stats = await check_stale_paddle_subscriptions()
        assert stats["checked"] == 1
        assert stats["renewed"] == 0

    @pytest.mark.asyncio
    @patch("payment_service.app.services.reconciliation.settings")
    @patch("httpx.AsyncClient")
    async def test_handles_fetch_failure_gracefully(self, mock_async_client, mock_settings):
        mock_settings.paddle_api_key = "test_key"
        mock_settings.subscription_service_url = "http://sub-service"
        mock_settings.internal_secret_token = "token"

        fail_response = MagicMock()
        fail_response.is_success = False
        fail_response.status_code = 500

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=fail_response)
        mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client.return_value.__aexit__ = AsyncMock(return_value=False)

        stats = await check_stale_paddle_subscriptions()
        assert stats["checked"] == 0
