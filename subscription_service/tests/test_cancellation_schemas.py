"""Tests for cancellation Pydantic schemas."""

from __future__ import annotations

import pytest
from datetime import datetime
from pydantic import ValidationError as PydanticValidationError

from app.schemas.cancellation import (
    CancelSubscriptionRequest,
    CancelSubscriptionResponse,
)


# ======================================================================
# CancelSubscriptionRequest
# ======================================================================


class TestCancelSubscriptionRequest:
    def test_defaults(self):
        """All fields should default to None/False."""
        schema = CancelSubscriptionRequest()
        assert schema.cancellation_reason is None
        assert schema.cancellation_comment is None
        assert schema.cancel_immediately is False

    def test_with_reason_only(self):
        schema = CancelSubscriptionRequest(cancellation_reason="too_expensive")
        assert schema.cancellation_reason == "too_expensive"
        assert schema.cancellation_comment is None
        assert schema.cancel_immediately is False

    def test_with_all_fields(self):
        schema = CancelSubscriptionRequest(
            cancellation_reason="not_using",
            cancellation_comment="I no longer need this service",
            cancel_immediately=True,
        )
        assert schema.cancellation_reason == "not_using"
        assert schema.cancellation_comment == "I no longer need this service"
        assert schema.cancel_immediately is True

    def test_reason_at_max_length(self):
        """Reason of exactly 32 characters must be accepted."""
        schema = CancelSubscriptionRequest(cancellation_reason="x" * 32)
        assert len(schema.cancellation_reason) == 32

    def test_reason_exceeds_max_length_raises(self):
        """Reason over 32 characters must be rejected."""
        with pytest.raises(PydanticValidationError):
            CancelSubscriptionRequest(cancellation_reason="x" * 33)

    def test_comment_at_max_length(self):
        """Comment of exactly 500 characters must be accepted."""
        schema = CancelSubscriptionRequest(cancellation_comment="y" * 500)
        assert len(schema.cancellation_comment) == 500

    def test_comment_exceeds_max_length_raises(self):
        """Comment over 500 characters must be rejected."""
        with pytest.raises(PydanticValidationError):
            CancelSubscriptionRequest(cancellation_comment="y" * 501)

    def test_cancel_immediately_explicit_false(self):
        schema = CancelSubscriptionRequest(cancel_immediately=False)
        assert schema.cancel_immediately is False

    def test_cancel_immediately_true(self):
        schema = CancelSubscriptionRequest(cancel_immediately=True)
        assert schema.cancel_immediately is True


# ======================================================================
# CancelSubscriptionResponse
# ======================================================================


class TestCancelSubscriptionResponse:
    def test_valid_full(self):
        now = datetime.utcnow()
        schema = CancelSubscriptionResponse(
            id=1,
            user_id="user_1",
            plan_code="professional",
            status="canceled",
            auto_renew=False,
            canceled_at=now,
            expires_at=now,
            cancellation_reason="too_expensive",
            access_ends_at=now,
            message="Subscription canceled immediately.",
        )
        assert schema.id == 1
        assert schema.auto_renew is False
        assert schema.status == "canceled"

    def test_valid_period_end_cancellation(self):
        now = datetime.utcnow()
        schema = CancelSubscriptionResponse(
            id=2,
            user_id="user_2",
            plan_code="basic",
            status="active",
            auto_renew=False,
            canceled_at=now,
            expires_at=now,
            cancellation_reason=None,
            access_ends_at=now,
            message="Subscription canceled. You'll have access until the end of period.",
        )
        assert schema.status == "active"
        assert schema.auto_renew is False
        assert schema.cancellation_reason is None

    def test_nullable_fields(self):
        schema = CancelSubscriptionResponse(
            id=3,
            user_id="user_3",
            plan_code="basic",
            status="canceled",
            auto_renew=False,
            canceled_at=None,
            expires_at=None,
            cancellation_reason=None,
            access_ends_at=None,
            message="Subscription canceled.",
        )
        assert schema.canceled_at is None
        assert schema.expires_at is None
        assert schema.access_ends_at is None

    def test_missing_required_fields_raises(self):
        with pytest.raises(PydanticValidationError):
            CancelSubscriptionResponse(
                id=1,
                user_id="user_1",
                # missing plan_code, status, auto_renew, message
            )
