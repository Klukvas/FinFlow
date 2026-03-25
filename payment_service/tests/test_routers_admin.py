"""Tests for the admin payments router.

Tests list_payments, get_payment_stats, list_failed_outbox_events,
and replay_outbox_event endpoints with mocked dependencies.
"""

from __future__ import annotations

import math
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4, UUID

from fastapi import HTTPException

from payment_service.app.models.models import Payment, PaymentStatus, PaymentProvider, PaymentPurpose
from payment_service.app.models.outbox import OutboxEvent
from payment_service.app.models.audit import AdminAuditLog
from payment_service.app.routers.admin_payments import (
    list_payments,
    get_payment_stats,
    list_failed_outbox_events,
    replay_outbox_event,
    _log_admin_action,
)


# ======================================================================
# _log_admin_action
# ======================================================================


class TestLogAdminAction:
    """Tests for the audit logging helper."""

    def test_creates_audit_log_entry(self):
        mock_db = MagicMock()
        admin_payload = {"sub": "admin_1"}
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        _log_admin_action(
            mock_db, admin_payload, "list_payments", "payment", mock_request,
            details={"total": 10},
        )

        mock_db.add.assert_called_once()
        added_obj = mock_db.add.call_args.args[0]
        assert isinstance(added_obj, AdminAuditLog)
        assert added_obj.admin_user_id == "admin_1"
        assert added_obj.action == "list_payments"
        assert added_obj.ip_address == "127.0.0.1"
        mock_db.commit.assert_called_once()

    def test_handles_no_client(self):
        mock_db = MagicMock()
        admin_payload = {"sub": "admin_2"}
        mock_request = MagicMock()
        mock_request.client = None

        _log_admin_action(
            mock_db, admin_payload, "get_stats", "payment", mock_request,
        )

        added_obj = mock_db.add.call_args.args[0]
        assert added_obj.ip_address is None


# ======================================================================
# list_payments
# ======================================================================


class TestListPayments:
    """Tests for the list_payments endpoint."""

    def _make_payment_mock(self, **kwargs):
        p = MagicMock(spec=Payment)
        p.id = kwargs.get("id", uuid4())
        p.provider = kwargs.get("provider", PaymentProvider.PADDLE)
        p.order_reference = kwargs.get("order_reference", "ORDER_test")
        p.user_id = kwargs.get("user_id", "user_1")
        p.workspace_id = kwargs.get("workspace_id", None)
        p.purpose = kwargs.get("purpose", PaymentPurpose.SUBSCRIPTION)
        p.plan_code = kwargs.get("plan_code", "pro")
        p.amount = kwargs.get("amount", 29.99)
        p.currency = kwargs.get("currency", "USD")
        p.status = kwargs.get("status", PaymentStatus.PAID)
        p.provider_payment_url = None
        p.paid_at = datetime.utcnow()
        p.failed_at = None
        p.refunded_at = None
        p.failure_reason = None
        p.extra_data = None
        p.created_at = datetime.utcnow()
        p.updated_at = datetime.utcnow()
        p.events = []
        return p

    def test_returns_paginated_response(self):
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        payment = self._make_payment_mock()

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [payment]
        mock_db.query.return_value = query_mock

        # Mock _log_admin_action (it calls db.add/commit)
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        result = list_payments(
            request=mock_request,
            status=None,
            user_id=None,
            page=1,
            page_size=20,
            admin={"sub": "admin_1"},
            db=mock_db,
        )

        assert result["total"] == 1
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert len(result["items"]) == 1

    def test_pagination_calculates_total_pages(self):
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 45
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        result = list_payments(
            request=mock_request,
            status=None,
            user_id=None,
            page=1,
            page_size=20,
            admin={"sub": "admin_1"},
            db=mock_db,
        )

        assert result["total_pages"] == 3  # ceil(45/20)

    def test_empty_total_returns_one_page(self):
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        result = list_payments(
            request=mock_request,
            status=None,
            user_id=None,
            page=1,
            page_size=20,
            admin={"sub": "admin_1"},
            db=mock_db,
        )

        assert result["total_pages"] == 1


# ======================================================================
# get_payment_stats
# ======================================================================


class TestGetPaymentStats:
    """Tests for the get_payment_stats endpoint."""

    def test_returns_stats_with_revenue(self):
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        # group_by query
        query_mock = MagicMock()
        query_mock.group_by.return_value = query_mock
        query_mock.all.return_value = [
            (PaymentStatus.PAID, 10),
            (PaymentStatus.FAILED, 3),
        ]
        mock_db.query.return_value = query_mock

        # revenue query (second db.query call)
        revenue_query = MagicMock()
        revenue_query.filter.return_value = revenue_query
        revenue_query.scalar.return_value = 299.90

        call_count = {"n": 0}
        original_query = mock_db.query

        def query_side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return query_mock
            return revenue_query

        mock_db.query.side_effect = query_side_effect
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        result = get_payment_stats(
            request=mock_request,
            admin={"sub": "admin_1"},
            db=mock_db,
        )

        assert result["total"] == 13
        assert result["by_status"]["PAID"] == 10
        assert result["by_status"]["FAILED"] == 3
        assert result["total_revenue"] == "299.9"


# ======================================================================
# replay_outbox_event
# ======================================================================


class TestReplayOutboxEvent:
    """Tests for the replay_outbox_event endpoint."""

    def test_replays_failed_event(self):
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        event_id = uuid4()
        event = MagicMock(spec=OutboxEvent)
        event.id = event_id
        event.status = "failed"
        event.event_type = "payment_success"
        event.aggregate_id = uuid4()
        event.retry_count = 5

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = event
        mock_db.query.return_value = query_mock
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        result = replay_outbox_event(
            event_id=str(event_id),
            request=mock_request,
            admin={"sub": "admin_1"},
            db=mock_db,
        )

        assert result["status"] == "replayed"
        assert event.status == "pending"
        assert event.retry_count == 0

    def test_invalid_event_id_raises_400(self):
        mock_db = MagicMock()
        mock_request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            replay_outbox_event(
                event_id="not-a-uuid",
                request=mock_request,
                admin={"sub": "admin_1"},
                db=mock_db,
            )
        assert exc_info.value.status_code == 400

    def test_event_not_found_raises_404(self):
        mock_db = MagicMock()
        mock_request = MagicMock()

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        mock_db.query.return_value = query_mock

        with pytest.raises(HTTPException) as exc_info:
            replay_outbox_event(
                event_id=str(uuid4()),
                request=mock_request,
                admin={"sub": "admin_1"},
                db=mock_db,
            )
        assert exc_info.value.status_code == 404

    def test_non_failed_event_raises_400(self):
        mock_db = MagicMock()
        mock_request = MagicMock()

        event = MagicMock(spec=OutboxEvent)
        event.status = "delivered"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = event
        mock_db.query.return_value = query_mock

        with pytest.raises(HTTPException) as exc_info:
            replay_outbox_event(
                event_id=str(uuid4()),
                request=mock_request,
                admin={"sub": "admin_1"},
                db=mock_db,
            )
        assert exc_info.value.status_code == 400


# ======================================================================
# list_failed_outbox_events
# ======================================================================


class TestListFailedOutboxEvents:
    """Tests for the list_failed_outbox_events endpoint."""

    def test_returns_paginated_failed_events(self):
        mock_db = MagicMock()
        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        event = MagicMock(spec=OutboxEvent)
        event.id = uuid4()
        event.aggregate_type = "payment"
        event.aggregate_id = uuid4()
        event.event_type = "payment_success"
        event.payload = {"user_id": "u1"}
        event.destination_url = "http://service/endpoint"
        event.status = "failed"
        event.retry_count = 10
        event.max_retries = 10
        event.last_error = "HTTP 500"
        event.created_at = datetime.utcnow()

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [event]
        mock_db.query.return_value = query_mock
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        result = list_failed_outbox_events(
            request=mock_request,
            event_type=None,
            page=1,
            page_size=20,
            admin={"sub": "admin_1"},
            db=mock_db,
        )

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["status"] == "failed"
