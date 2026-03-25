"""Shared fixtures for subscription_service tests."""

from __future__ import annotations

import os

# Set required env vars before any subscription_service imports trigger Settings()
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
os.environ.setdefault("internal_secret_token", "test-internal-secret")
os.environ.setdefault("jwt_secret_key", "test-jwt-secret")
os.environ.setdefault("redis_url", "redis://localhost:6379/0")

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Database mock
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy session with chainable query builder."""
    db = MagicMock()

    query_mock = MagicMock()
    query_mock.filter.return_value = query_mock
    query_mock.filter_by.return_value = query_mock
    query_mock.join.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.offset.return_value = query_mock
    query_mock.first.return_value = None
    query_mock.all.return_value = []
    query_mock.count.return_value = 0
    query_mock.delete.return_value = 0
    query_mock.group_by.return_value = query_mock

    db.query.return_value = query_mock
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.flush = MagicMock()
    db.rollback = MagicMock()

    return db


# ---------------------------------------------------------------------------
# Redis mock
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    r = MagicMock()
    r.get.return_value = None
    r.setex = MagicMock()
    r.delete = MagicMock(return_value=0)
    r.scan.return_value = (0, [])
    r.publish = MagicMock()
    pipeline = MagicMock()
    pipeline.__enter__ = MagicMock(return_value=pipeline)
    pipeline.__exit__ = MagicMock(return_value=False)
    r.pipeline.return_value = pipeline
    return r


# ---------------------------------------------------------------------------
# Model factories
# ---------------------------------------------------------------------------


@pytest.fixture
def make_plan():
    """Factory fixture that builds Plan model instances."""

    def _make(
        id: int = 1,
        code: str = "professional",
        name: str = "Professional",
        period_days: int = 30,
        price: Decimal | None = Decimal("29.99"),
        currency: str = "USD",
        is_active: bool = True,
        version: int = 1,
        features: list | None = None,
    ):
        plan = MagicMock()
        plan.id = id
        plan.code = code
        plan.name = name
        plan.period_days = period_days
        plan.price = price
        plan.currency = currency
        plan.is_active = is_active
        plan.version = version
        plan.features = features or []
        plan.created_at = datetime.utcnow()
        plan.updated_at = datetime.utcnow()
        return plan

    return _make


@pytest.fixture
def make_subscription():
    """Factory fixture that builds Subscription model instances."""

    def _make(
        id: int = 1,
        user_id: str = "user_test_1",
        plan_code: str = "professional",
        status: str = "active",
        started_at: datetime | None = None,
        expires_at: datetime | None = None,
        canceled_at: datetime | None = None,
        auto_renew: bool = True,
        recurring_token: str | None = None,
        payment_provider: str | None = None,
        last_payment_id: str | None = None,
        next_billing_date: datetime | None = None,
        paddle_customer_id: str | None = None,
        paddle_subscription_id: str | None = None,
        paddle_price_id: str | None = None,
        consent_given: bool = False,
        consent_version: str | None = None,
        consent_timestamp: datetime | None = None,
        consent_ip_address: str | None = None,
        consent_user_agent: str | None = None,
        cancellation_reason: str | None = None,
        cancellation_comment: str | None = None,
        cancellation_ip_address: str | None = None,
    ):
        sub = MagicMock()
        sub.id = id
        sub.user_id = user_id
        sub.plan_code = plan_code
        sub.status = status
        sub.started_at = started_at or datetime.utcnow()
        sub.expires_at = expires_at or (datetime.utcnow() + timedelta(days=30))
        sub.canceled_at = canceled_at
        sub.auto_renew = auto_renew
        sub.recurring_token = recurring_token
        sub.payment_provider = payment_provider
        sub.last_payment_id = last_payment_id
        sub.next_billing_date = next_billing_date
        sub.paddle_customer_id = paddle_customer_id
        sub.paddle_subscription_id = paddle_subscription_id
        sub.paddle_price_id = paddle_price_id
        sub.consent_given = consent_given
        sub.consent_version = consent_version
        sub.consent_timestamp = consent_timestamp
        sub.consent_ip_address = consent_ip_address
        sub.consent_user_agent = consent_user_agent
        sub.cancellation_reason = cancellation_reason
        sub.cancellation_comment = cancellation_comment
        sub.cancellation_ip_address = cancellation_ip_address
        sub.created_at = datetime.utcnow()
        sub.updated_at = datetime.utcnow()
        return sub

    return _make


@pytest.fixture
def make_feature():
    """Factory fixture that builds Feature model instances."""

    def _make(
        id: int = 1,
        code: str = "accounts",
        name: str = "Accounts",
        description: str | None = "Manage accounts",
    ):
        feat = MagicMock()
        feat.id = id
        feat.code = code
        feat.name = name
        feat.description = description
        return feat

    return _make


@pytest.fixture
def make_plan_feature():
    """Factory fixture that builds PlanFeature model instances."""

    def _make(
        id: int = 1,
        plan_id: int = 1,
        feature_code: str = "accounts",
        enabled: bool = True,
        limit_value: int | None = 5,
    ):
        pf = MagicMock()
        pf.id = id
        pf.plan_id = plan_id
        pf.feature_code = feature_code
        pf.enabled = enabled
        pf.limit_value = limit_value
        return pf

    return _make


@pytest.fixture
def make_consent_log():
    """Factory fixture that builds SubscriptionConsentLog instances."""

    def _make(
        id: int = 1,
        subscription_id: int = 1,
        user_id: str = "user_test_1",
        consent_version: str = "v1.0.0",
        consent_text: str = "I agree to subscribe...",
        consent_language: str = "en",
        consent_given_at: datetime | None = None,
        ip_address: str = "127.0.0.1",
        user_agent: str = "TestBrowser/1.0",
        browser_fingerprint: str | None = None,
        consent_metadata: dict | None = None,
    ):
        log = MagicMock()
        log.id = id
        log.subscription_id = subscription_id
        log.user_id = user_id
        log.consent_version = consent_version
        log.consent_text = consent_text
        log.consent_language = consent_language
        log.consent_given_at = consent_given_at or datetime.utcnow()
        log.ip_address = ip_address
        log.user_agent = user_agent
        log.browser_fingerprint = browser_fingerprint
        log.consent_metadata = consent_metadata
        log.created_at = datetime.utcnow()
        return log

    return _make


# ---------------------------------------------------------------------------
# FastAPI TestClient
# ---------------------------------------------------------------------------


@pytest.fixture
def test_client():
    """FastAPI TestClient with mocked dependencies.

    Patches database, redis, and GeoIP middleware so the app can start
    without any real infrastructure.
    """
    with (
        patch("app.database.create_engine"),
        patch("app.database.sessionmaker"),
        patch("app.database.SessionLocal"),
        patch("shared.geoip.GeoIPMiddleware", lambda *a, **kw: None),
        patch("app.main.GeoIPMiddleware"),
        patch("app.utils.logging.setup_logging"),
    ):
        from fastapi.testclient import TestClient
        from app.main import create_app

        application = create_app()
        yield TestClient(application)
