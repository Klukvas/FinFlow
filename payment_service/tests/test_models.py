"""Tests for SQLAlchemy models: audit, models, outbox.

Verifies table names, columns, defaults, constraints, enums, and relationships.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from unittest.mock import MagicMock, patch

from payment_service.app.models.audit import AdminAuditLog
from payment_service.app.models.models import (
    Payment,
    PaymentEvent,
    PaymentStatus,
    PaymentProvider,
    PaymentPurpose,
    PaymentEventType,
    ProcessedWebhookEvent,
    PaddlePriceMap,
    IdempotencyKey,
)
from payment_service.app.models.outbox import OutboxEvent


# ======================================================================
# Enum values
# ======================================================================


class TestPaymentEnums:
    """Verify all enum members are defined correctly."""

    def test_payment_provider_values(self):
        assert PaymentProvider.WAYFORPAY == "WAYFORPAY"
        assert PaymentProvider.PADDLE == "PADDLE"
        assert len(PaymentProvider) == 2

    def test_payment_purpose_values(self):
        assert PaymentPurpose.SUBSCRIPTION == "SUBSCRIPTION"
        assert PaymentPurpose.ONE_TIME == "ONE_TIME"
        assert len(PaymentPurpose) == 2

    def test_payment_status_values(self):
        expected = {
            "CREATED", "PENDING", "PAID", "FAILED",
            "EXPIRED", "REFUNDED", "PARTIALLY_REFUNDED", "CANCELED",
        }
        actual = {s.value for s in PaymentStatus}
        assert actual == expected

    def test_payment_event_type_values(self):
        expected = {"CREATED", "CALLBACK", "STATUS_CHANGE", "REFUND", "VERIFICATION"}
        actual = {t.value for t in PaymentEventType}
        assert actual == expected

    def test_enums_are_str_subclass(self):
        """Enum values must be usable as strings for JSON serialisation."""
        assert isinstance(PaymentProvider.PADDLE, str)
        assert isinstance(PaymentPurpose.SUBSCRIPTION, str)
        assert isinstance(PaymentStatus.PAID, str)
        assert isinstance(PaymentEventType.CREATED, str)


# ======================================================================
# AdminAuditLog
# ======================================================================


class TestAdminAuditLog:
    """Tests for AdminAuditLog model."""

    def test_tablename(self):
        assert AdminAuditLog.__tablename__ == "admin_audit_log"

    def test_has_required_columns(self):
        column_names = {c.name for c in AdminAuditLog.__table__.columns}
        required = {"id", "admin_user_id", "action", "resource_type", "created_at"}
        assert required.issubset(column_names)

    def test_has_optional_columns(self):
        column_names = {c.name for c in AdminAuditLog.__table__.columns}
        optional = {"resource_id", "details", "ip_address"}
        assert optional.issubset(column_names)

    def test_admin_user_id_not_nullable(self):
        col = AdminAuditLog.__table__.c.admin_user_id
        assert col.nullable is False

    def test_resource_id_nullable(self):
        col = AdminAuditLog.__table__.c.resource_id
        assert col.nullable is True

    def test_ip_address_nullable(self):
        col = AdminAuditLog.__table__.c.ip_address
        assert col.nullable is True

    def test_admin_user_id_indexed(self):
        col = AdminAuditLog.__table__.c.admin_user_id
        assert col.index is True


# ======================================================================
# Payment model
# ======================================================================


class TestPaymentModel:
    """Tests for Payment model."""

    def test_tablename(self):
        assert Payment.__tablename__ == "payments"

    def test_has_all_expected_columns(self):
        column_names = {c.name for c in Payment.__table__.columns}
        expected = {
            "id", "provider", "order_reference", "user_id", "workspace_id",
            "purpose", "plan_code", "amount", "currency", "status",
            "provider_payment_url", "provider_payload", "provider_response",
            "recurring_token", "is_recurring",
            "paddle_customer_id", "paddle_subscription_id", "paddle_transaction_id",
            "paid_at", "failed_at", "refunded_at", "failure_reason",
            "extra_data", "created_at", "updated_at",
        }
        assert expected.issubset(column_names)

    def test_user_id_not_nullable(self):
        col = Payment.__table__.c.user_id
        assert col.nullable is False

    def test_workspace_id_nullable(self):
        col = Payment.__table__.c.workspace_id
        assert col.nullable is True

    def test_order_reference_unique(self):
        col = Payment.__table__.c.order_reference
        assert col.unique is True

    def test_is_recurring_default_false(self):
        col = Payment.__table__.c.is_recurring
        assert col.default.arg is False

    def test_events_relationship_exists(self):
        """Payment must have a 'events' relationship to PaymentEvent."""
        assert hasattr(Payment, "events")

    def test_table_has_check_constraints(self):
        constraints = Payment.__table__.constraints
        constraint_names = {c.name for c in constraints if hasattr(c, "name") and c.name}
        assert "ck_payment_status" in constraint_names
        assert "ck_payment_provider" in constraint_names
        assert "ck_payment_purpose" in constraint_names


# ======================================================================
# PaymentEvent model
# ======================================================================


class TestPaymentEventModel:
    """Tests for PaymentEvent model."""

    def test_tablename(self):
        assert PaymentEvent.__tablename__ == "payment_events"

    def test_has_required_columns(self):
        column_names = {c.name for c in PaymentEvent.__table__.columns}
        expected = {
            "id", "payment_id", "event_type", "provider_event_id",
            "signature_valid", "payload_raw", "status_before", "status_after",
            "created_at",
        }
        assert expected.issubset(column_names)

    def test_payment_id_not_nullable(self):
        col = PaymentEvent.__table__.c.payment_id
        assert col.nullable is False

    def test_payload_raw_not_nullable(self):
        col = PaymentEvent.__table__.c.payload_raw
        assert col.nullable is False

    def test_payment_relationship_exists(self):
        assert hasattr(PaymentEvent, "payment")


# ======================================================================
# ProcessedWebhookEvent model
# ======================================================================


class TestProcessedWebhookEventModel:
    """Tests for ProcessedWebhookEvent model."""

    def test_tablename(self):
        assert ProcessedWebhookEvent.__tablename__ == "processed_webhook_events"

    def test_event_id_unique(self):
        col = ProcessedWebhookEvent.__table__.c.event_id
        assert col.unique is True

    def test_event_id_not_nullable(self):
        col = ProcessedWebhookEvent.__table__.c.event_id
        assert col.nullable is False

    def test_payload_hash_not_nullable(self):
        col = ProcessedWebhookEvent.__table__.c.payload_hash
        assert col.nullable is False


# ======================================================================
# PaddlePriceMap model
# ======================================================================


class TestPaddlePriceMapModel:
    """Tests for PaddlePriceMap model."""

    def test_tablename(self):
        assert PaddlePriceMap.__tablename__ == "paddle_price_map"

    def test_plan_code_unique(self):
        col = PaddlePriceMap.__table__.c.plan_code
        assert col.unique is True

    def test_is_active_default_true(self):
        col = PaddlePriceMap.__table__.c.is_active
        assert col.default.arg is True

    def test_billing_period_default_monthly(self):
        col = PaddlePriceMap.__table__.c.billing_period
        assert col.default.arg == "monthly"

    def test_amount_nullable(self):
        col = PaddlePriceMap.__table__.c.amount
        assert col.nullable is True


# ======================================================================
# IdempotencyKey model
# ======================================================================


class TestIdempotencyKeyModel:
    """Tests for IdempotencyKey model."""

    def test_tablename(self):
        assert IdempotencyKey.__tablename__ == "idempotency_keys"

    def test_key_is_primary_key(self):
        col = IdempotencyKey.__table__.c.key
        assert col.primary_key is True

    def test_scope_not_nullable(self):
        col = IdempotencyKey.__table__.c.scope
        assert col.nullable is False

    def test_request_hash_not_nullable(self):
        col = IdempotencyKey.__table__.c.request_hash
        assert col.nullable is False

    def test_expires_at_not_nullable(self):
        col = IdempotencyKey.__table__.c.expires_at
        assert col.nullable is False


# ======================================================================
# OutboxEvent model
# ======================================================================


class TestOutboxEventModel:
    """Tests for OutboxEvent model."""

    def test_tablename(self):
        assert OutboxEvent.__tablename__ == "outbox_events"

    def test_has_required_columns(self):
        column_names = {c.name for c in OutboxEvent.__table__.columns}
        expected = {
            "id", "aggregate_type", "aggregate_id", "event_type", "payload",
            "destination_url", "headers", "status", "retry_count", "max_retries",
            "next_retry_at", "last_error", "created_at", "delivered_at",
        }
        assert expected.issubset(column_names)

    def test_status_default_pending(self):
        col = OutboxEvent.__table__.c.status
        assert col.default.arg == "pending"

    def test_retry_count_default_zero(self):
        col = OutboxEvent.__table__.c.retry_count
        assert col.default.arg == 0

    def test_max_retries_default_ten(self):
        col = OutboxEvent.__table__.c.max_retries
        assert col.default.arg == 10

    def test_destination_url_not_nullable(self):
        col = OutboxEvent.__table__.c.destination_url
        assert col.nullable is False

    def test_payload_not_nullable(self):
        col = OutboxEvent.__table__.c.payload
        assert col.nullable is False

    def test_headers_nullable(self):
        col = OutboxEvent.__table__.c.headers
        assert col.nullable is True

    def test_delivered_at_nullable(self):
        col = OutboxEvent.__table__.c.delivered_at
        assert col.nullable is True

    def test_has_status_check_constraint(self):
        constraints = OutboxEvent.__table__.constraints
        constraint_names = {c.name for c in constraints if hasattr(c, "name") and c.name}
        assert "ck_outbox_status" in constraint_names
