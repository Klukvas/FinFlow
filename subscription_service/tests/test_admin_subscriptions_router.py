"""Tests for admin subscription management router endpoints."""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.routers.admin_subscriptions import (
    list_subscriptions,
    get_subscription_stats,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_chainable_query(count: int = 0, items: list | None = None):
    """Build a fully chainable query mock for admin subscriptions listing."""
    query = MagicMock()
    query.filter.return_value = query
    query.count.return_value = count
    query.order_by.return_value = query
    query.offset.return_value = query
    query.limit.return_value = query
    query.all.return_value = items or []
    return query


# ---------------------------------------------------------------------------
# list_subscriptions
# ---------------------------------------------------------------------------


class TestListSubscriptions:
    """Tests for GET /admin/subscriptions."""

    def test_returns_paginated_list_no_filters(self, mock_db, make_subscription):
        sub1 = make_subscription(id=1, user_id="user_1")
        sub2 = make_subscription(id=2, user_id="user_2")

        query = _build_chainable_query(count=2, items=[sub1, sub2])
        mock_db.query.return_value = query

        admin = {"sub": "admin_1"}
        result = list_subscriptions(
            status=None, plan_code=None, user_id=None,
            page=1, page_size=20, admin=admin, db=mock_db,
        )

        assert result.total == 2
        assert result.page == 1
        assert result.page_size == 20
        assert result.total_pages == 1
        assert len(result.items) == 2

    def test_filters_by_status(self, mock_db, make_subscription):
        sub = make_subscription(status="canceled")
        query = _build_chainable_query(count=1, items=[sub])
        mock_db.query.return_value = query

        admin = {"sub": "admin_1"}
        result = list_subscriptions(
            status="canceled", plan_code=None, user_id=None,
            page=1, page_size=20, admin=admin, db=mock_db,
        )

        assert result.total == 1

    def test_filters_by_plan_code(self, mock_db, make_subscription):
        subs = [make_subscription(id=i, plan_code="basic") for i in range(1, 6)]
        query = _build_chainable_query(count=5, items=subs)
        mock_db.query.return_value = query

        admin = {"sub": "admin_1"}
        result = list_subscriptions(
            status=None, plan_code="basic", user_id=None,
            page=1, page_size=20, admin=admin, db=mock_db,
        )

        assert result.total == 5

    def test_filters_by_user_id(self, mock_db, make_subscription):
        sub = make_subscription(user_id="target_user")
        query = _build_chainable_query(count=1, items=[sub])
        mock_db.query.return_value = query

        admin = {"sub": "admin_1"}
        result = list_subscriptions(
            status=None, plan_code=None, user_id="target_user",
            page=1, page_size=20, admin=admin, db=mock_db,
        )

        assert result.total == 1

    def test_pagination_calculates_offset(self, mock_db):
        query = _build_chainable_query(count=50, items=[])
        mock_db.query.return_value = query

        admin = {"sub": "admin_1"}
        result = list_subscriptions(
            status=None, plan_code=None, user_id=None,
            page=3, page_size=10, admin=admin, db=mock_db,
        )

        assert result.total == 50
        assert result.page == 3
        assert result.page_size == 10
        assert result.total_pages == 5

    def test_empty_list(self, mock_db):
        query = _build_chainable_query(count=0, items=[])
        mock_db.query.return_value = query

        admin = {"sub": "admin_1"}
        result = list_subscriptions(
            status=None, plan_code=None, user_id=None,
            page=1, page_size=20, admin=admin, db=mock_db,
        )

        assert result.total == 0
        assert result.total_pages == 1
        assert len(result.items) == 0

    def test_total_pages_rounds_up(self, mock_db):
        query = _build_chainable_query(count=21, items=[])
        mock_db.query.return_value = query

        admin = {"sub": "admin_1"}
        result = list_subscriptions(
            status=None, plan_code=None, user_id=None,
            page=1, page_size=10, admin=admin, db=mock_db,
        )

        assert result.total_pages == 3  # ceil(21/10) = 3

    def test_combines_multiple_filters(self, mock_db, make_subscription):
        sub = make_subscription(status="active", plan_code="professional", user_id="user_1")
        query = _build_chainable_query(count=1, items=[sub])
        mock_db.query.return_value = query

        admin = {"sub": "admin_1"}
        result = list_subscriptions(
            status="active", plan_code="professional", user_id="user_1",
            page=1, page_size=20, admin=admin, db=mock_db,
        )

        assert result.total == 1


# ---------------------------------------------------------------------------
# get_subscription_stats
# ---------------------------------------------------------------------------


class TestGetSubscriptionStats:
    """Tests for GET /admin/subscriptions/stats."""

    def test_returns_stats(self, mock_db):
        query = MagicMock()
        query.group_by.return_value.all.return_value = [
            ("active", 80),
            ("past_due", 10),
            ("canceled", 8),
            ("paused", 2),
        ]
        mock_db.query.return_value = query

        admin = {"sub": "admin_1"}
        result = get_subscription_stats(admin=admin, db=mock_db)

        assert result.total == 100
        assert result.active == 80
        assert result.past_due == 10
        assert result.canceled == 8
        assert result.paused == 2

    def test_returns_zeros_when_no_subscriptions(self, mock_db):
        query = MagicMock()
        query.group_by.return_value.all.return_value = []
        mock_db.query.return_value = query

        admin = {"sub": "admin_1"}
        result = get_subscription_stats(admin=admin, db=mock_db)

        assert result.total == 0
        assert result.active == 0
        assert result.past_due == 0
        assert result.canceled == 0
        assert result.paused == 0

    def test_handles_partial_statuses(self, mock_db):
        """Must handle cases where some statuses have no subscriptions."""
        query = MagicMock()
        query.group_by.return_value.all.return_value = [
            ("active", 50),
        ]
        mock_db.query.return_value = query

        admin = {"sub": "admin_1"}
        result = get_subscription_stats(admin=admin, db=mock_db)

        assert result.total == 50
        assert result.active == 50
        assert result.past_due == 0
        assert result.canceled == 0
        assert result.paused == 0
