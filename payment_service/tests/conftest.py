"""Shared fixtures for payment_service Paddle Billing tests."""

from __future__ import annotations

import os

# Set required env vars before any payment_service imports trigger Settings()
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")
os.environ.setdefault("internal_secret_token", "test-secret-token")

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from uuid import uuid4, UUID


# ---------------------------------------------------------------------------
# Database mock
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """Mock SQLAlchemy session.

    Provides chainable query/filter/first/all behaviour by default.
    Individual tests can override return values where needed.
    """
    db = MagicMock()

    # Chainable query builder
    query_mock = MagicMock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.limit.return_value = query_mock
    query_mock.offset.return_value = query_mock
    query_mock.first.return_value = None
    query_mock.all.return_value = []
    query_mock.count.return_value = 0

    db.query.return_value = query_mock
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()

    return db


# ---------------------------------------------------------------------------
# PaddleClient fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def paddle_client():
    """PaddleClient initialised with deterministic test configuration."""
    with patch("payment_service.app.clients.paddle_client.settings") as mock_settings:
        mock_settings.paddle_api_key = "test_api_key"
        mock_settings.paddle_webhook_secret = "test_webhook_secret"
        mock_settings.paddle_environment = "sandbox"
        mock_settings.paddle_success_url = "http://localhost:3000/payment/return"
        mock_settings.paddle_cancel_url = "http://localhost:3000/pricing"

        from payment_service.app.clients.paddle_client import PaddleClient
        yield PaddleClient()


# ---------------------------------------------------------------------------
# Mock PaddleClient (for PaymentService tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_paddle_client():
    """A fully mocked PaddleClient instance."""
    client = MagicMock()
    client.create_checkout_session = AsyncMock(return_value={
        "checkout_url": "https://checkout.paddle.com/test-session",
        "transaction_id": "txn_test_abc123",
    })
    client.verify_webhook_signature = MagicMock(return_value=True)
    client.cancel_subscription = AsyncMock(return_value={"status": "canceled"})
    client.get_subscription = AsyncMock(return_value={
        "id": "sub_test_1",
        "status": "active",
        "items": [{"price": {"id": "pri_old_plan"}, "quantity": 1}],
    })
    client.get_transaction = AsyncMock(return_value={"id": "txn_test_1", "status": "completed"})
    client.update_subscription = AsyncMock(return_value={
        "id": "sub_test_1",
        "status": "active",
        "items": [{"price": {"id": "pri_new_plan"}, "quantity": 1}],
    })
    return client


# ---------------------------------------------------------------------------
# Mock SubscriptionClient (for PaymentService tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_subscription_client():
    """A fully mocked SubscriptionClient instance."""
    client = MagicMock()
    client.notify_payment_success = AsyncMock(return_value=True)
    client.notify_payment_failure = AsyncMock(return_value=True)
    client.notify_payment_refunded = AsyncMock(return_value=True)
    client.notify_paddle_subscription_event = AsyncMock(return_value=True)
    return client


# ---------------------------------------------------------------------------
# PaymentService with mocked dependencies
# ---------------------------------------------------------------------------

@pytest.fixture
def payment_service(mock_db, mock_paddle_client, mock_subscription_client):
    """PaymentService with mocked DB, PaddleClient, and SubscriptionClient.

    Dependencies are injected by patching the constructors so the real
    ``__init__`` never touches settings or the database.
    """
    with (
        patch("payment_service.app.services.payment_service.PaddleClient", return_value=mock_paddle_client),
        patch("payment_service.app.services.payment_service.SubscriptionClient", return_value=mock_subscription_client),
        patch("payment_service.app.services.payment_service.settings") as mock_settings,
    ):
        mock_settings.paddle_success_url = "http://localhost:3000/payment/return"

        from payment_service.app.services.payment_service import PaymentService
        svc = PaymentService(mock_db)

    return svc


# ---------------------------------------------------------------------------
# Sample webhook event factory
# ---------------------------------------------------------------------------

@pytest.fixture
def make_webhook_event():
    """Factory fixture that builds PaddleWebhookEvent instances."""

    def _make(
        event_type: str = "transaction.completed",
        event_id: str | None = None,
        data: dict | None = None,
    ):
        from payment_service.app.schemas.payment import PaddleWebhookEvent
        return PaddleWebhookEvent(
            event_id=event_id or f"evt_{uuid4().hex[:12]}",
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            notification_id=f"ntf_{uuid4().hex[:12]}",
            data=data or {},
        )

    return _make


# ---------------------------------------------------------------------------
# Sample Payment model object factory
# ---------------------------------------------------------------------------

@pytest.fixture
def make_payment():
    """Factory fixture that builds Payment model instances."""

    def _make(
        payment_id: UUID | None = None,
        user_id: str = "user_test_1",
        workspace_id: str | None = "ws_test_1",
        plan_code: str = "professional",
        amount: Decimal = Decimal("29.99"),
        currency: str = "USD",
        status: str = "CREATED",
        order_reference: str | None = None,
        paddle_customer_id: str | None = None,
        paddle_subscription_id: str | None = None,
        paddle_transaction_id: str | None = None,
    ):
        from payment_service.app.models.models import (
            Payment,
            PaymentStatus,
            PaymentProvider,
            PaymentPurpose,
        )
        return Payment(
            id=payment_id or uuid4(),
            provider=PaymentProvider.PADDLE,
            order_reference=order_reference or f"ORDER_test_{uuid4().hex[:8]}",
            user_id=user_id,
            workspace_id=workspace_id,
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code=plan_code,
            amount=amount,
            currency=currency,
            status=PaymentStatus[status],
            paddle_customer_id=paddle_customer_id,
            paddle_subscription_id=paddle_subscription_id,
            paddle_transaction_id=paddle_transaction_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    return _make
