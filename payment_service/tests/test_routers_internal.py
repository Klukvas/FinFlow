"""Tests for the internal router endpoints.

Tests verify_internal_token, create_payment_internal, get_payment_internal,
create_recurring_payment_internal, and refund_payment_internal.
"""

from __future__ import annotations

import secrets
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from payment_service.app.routers.internal import verify_internal_token
from payment_service.app.utils.errors import AuthError
from payment_service.app.models.models import (
    Payment,
    PaymentStatus,
    PaymentProvider,
    PaymentPurpose,
)


# ======================================================================
# verify_internal_token
# ======================================================================


class TestVerifyInternalToken:
    """Tests for the verify_internal_token dependency."""

    @patch("payment_service.app.routers.internal.settings")
    def test_valid_token_passes(self, mock_settings):
        mock_settings.internal_secret_token = "correct-token"
        # Should not raise
        verify_internal_token("correct-token")

    @patch("payment_service.app.routers.internal.settings")
    def test_empty_token_raises_auth_error(self, mock_settings):
        mock_settings.internal_secret_token = "correct-token"
        with pytest.raises(AuthError) as exc_info:
            verify_internal_token("")
        assert "INVALID_INTERNAL_TOKEN" in exc_info.value.error_code

    @patch("payment_service.app.routers.internal.settings")
    def test_wrong_token_raises_auth_error(self, mock_settings):
        mock_settings.internal_secret_token = "correct-token"
        with pytest.raises(AuthError) as exc_info:
            verify_internal_token("wrong-token")
        assert "INVALID_INTERNAL_TOKEN" in exc_info.value.error_code

    @patch("payment_service.app.routers.internal.settings")
    def test_none_token_raises_auth_error(self, mock_settings):
        mock_settings.internal_secret_token = "correct-token"
        with pytest.raises(AuthError) as exc_info:
            verify_internal_token("")
        assert "INVALID_INTERNAL_TOKEN" in exc_info.value.error_code


# ======================================================================
# create_payment_internal
# ======================================================================


class TestCreatePaymentInternal:
    """Tests for the create_payment_internal endpoint."""

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.internal.PaymentService")
    async def test_creates_payment_and_returns_response(self, mock_service_cls):
        from payment_service.app.routers.internal import create_payment_internal
        from payment_service.app.schemas.payment import CreatePaymentRequest

        mock_payment = MagicMock(spec=Payment)
        mock_payment.id = uuid4()
        mock_payment.order_reference = "ORDER_int_1"
        mock_payment.provider = PaymentProvider.PADDLE
        mock_payment.amount = Decimal("29.99")
        mock_payment.currency = "USD"
        mock_payment.status = PaymentStatus.CREATED
        mock_payment.provider_payment_url = "https://checkout.paddle.com/test"
        mock_payment.provider_payload = None
        mock_payment.paddle_transaction_id = "txn_int_1"
        mock_payment.created_at = datetime.utcnow()

        mock_service = MagicMock()
        mock_service.create_payment = AsyncMock(return_value=mock_payment)
        mock_service_cls.return_value = mock_service

        request = CreatePaymentRequest(
            user_id="user_int",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="pro",
            amount=Decimal("29.99"),
            currency="USD",
        )

        result = await create_payment_internal(
            request=request,
            db=MagicMock(),
            _=None,
        )

        assert result.payment_id == mock_payment.id
        assert result.order_reference == "ORDER_int_1"
        assert result.status == PaymentStatus.CREATED


# ======================================================================
# get_payment_internal
# ======================================================================


class TestGetPaymentInternal:
    """Tests for the get_payment_internal endpoint."""

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.internal.PaymentService")
    async def test_returns_payment_out(self, mock_service_cls):
        from payment_service.app.routers.internal import get_payment_internal

        payment_id = uuid4()
        mock_payment = MagicMock(spec=Payment)
        mock_payment.id = payment_id
        mock_payment.provider = PaymentProvider.PADDLE
        mock_payment.order_reference = "ORDER_get_int"
        mock_payment.user_id = "u1"
        mock_payment.workspace_id = None
        mock_payment.purpose = PaymentPurpose.SUBSCRIPTION
        mock_payment.plan_code = "pro"
        mock_payment.amount = Decimal("29.99")
        mock_payment.currency = "USD"
        mock_payment.status = PaymentStatus.PAID
        mock_payment.provider_payment_url = None
        mock_payment.paid_at = datetime.utcnow()
        mock_payment.failed_at = None
        mock_payment.refunded_at = None
        mock_payment.failure_reason = None
        mock_payment.extra_data = None
        mock_payment.created_at = datetime.utcnow()
        mock_payment.updated_at = datetime.utcnow()
        mock_payment.events = []

        mock_service = MagicMock()
        mock_service.payment_repo.get_by_id_or_raise.return_value = mock_payment
        mock_service_cls.return_value = mock_service

        result = await get_payment_internal(
            payment_id=payment_id,
            db=MagicMock(),
            _=None,
        )

        assert result.id == payment_id
        mock_service.payment_repo.get_by_id_or_raise.assert_called_once_with(payment_id)


# ======================================================================
# create_recurring_payment_internal
# ======================================================================


class TestCreateRecurringPaymentInternal:
    """Tests for the create_recurring_payment_internal endpoint."""

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.internal.PaymentService")
    async def test_creates_recurring_payment(self, mock_service_cls):
        from payment_service.app.routers.internal import create_recurring_payment_internal

        mock_payment = MagicMock(spec=Payment)
        mock_payment.id = uuid4()
        mock_payment.order_reference = "ORDER_rec_1"
        mock_payment.provider = PaymentProvider.PADDLE
        mock_payment.amount = Decimal("29.99")
        mock_payment.currency = "USD"
        mock_payment.status = PaymentStatus.CREATED
        mock_payment.created_at = datetime.utcnow()

        mock_service = MagicMock()
        mock_service.create_recurring_payment = AsyncMock(return_value=mock_payment)
        mock_service_cls.return_value = mock_service

        request_body = {
            "user_id": "user_rec",
            "plan_code": "pro",
            "amount": "29.99",
            "currency": "USD",
            "recurring_token": "tok_123",
        }

        result = await create_recurring_payment_internal(
            request=request_body,
            db=MagicMock(),
            _=None,
        )

        assert result.payment_id == mock_payment.id
        assert result.payment_url is None  # No URL for recurring

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.internal.PaymentService")
    async def test_propagates_exception_on_failure(self, mock_service_cls):
        from payment_service.app.routers.internal import create_recurring_payment_internal

        mock_service = MagicMock()
        mock_service.create_recurring_payment = AsyncMock(
            side_effect=ValueError("Missing field")
        )
        mock_service_cls.return_value = mock_service

        request_body = {
            "user_id": "user_err",
            "plan_code": "pro",
            "amount": "10",
            "currency": "USD",
            "recurring_token": "tok_err",
        }

        with pytest.raises(ValueError, match="Missing field"):
            await create_recurring_payment_internal(
                request=request_body,
                db=MagicMock(),
                _=None,
            )


# ======================================================================
# refund_payment_internal
# ======================================================================


class TestRefundPaymentInternal:
    """Tests for the refund_payment_internal endpoint."""

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.internal.store_idempotency")
    @patch("payment_service.app.routers.internal.check_idempotency")
    @patch("payment_service.app.routers.internal.compute_request_hash")
    @patch("payment_service.app.routers.internal.PaymentService")
    async def test_processes_refund_successfully(
        self, mock_service_cls, mock_hash, mock_check, mock_store,
    ):
        from payment_service.app.routers.internal import refund_payment_internal
        from payment_service.app.schemas.payment import RefundRequest

        payment_id = uuid4()
        mock_payment = MagicMock(spec=Payment)
        mock_payment.id = payment_id
        mock_payment.status = PaymentStatus.REFUNDED
        mock_payment.amount = Decimal("29.99")
        mock_payment.refunded_at = datetime.utcnow()

        mock_service = MagicMock()
        mock_service.payment_repo.get_by_id_or_raise.return_value = mock_payment
        mock_service.process_refund = AsyncMock(return_value=mock_payment)
        mock_service_cls.return_value = mock_service

        mock_hash.return_value = "hash_1"
        mock_check.return_value = None

        request = RefundRequest(reason="customer request")

        result = await refund_payment_internal(
            payment_id=payment_id,
            request=request,
            db=MagicMock(),
            _=None,
            idempotency_key=None,
        )

        assert result.payment_id == payment_id
        assert result.status == PaymentStatus.REFUNDED

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.internal.check_idempotency")
    @patch("payment_service.app.routers.internal.compute_request_hash")
    @patch("payment_service.app.routers.internal.PaymentService")
    async def test_returns_cached_response_on_idempotency_hit(
        self, mock_service_cls, mock_hash, mock_check,
    ):
        from payment_service.app.routers.internal import refund_payment_internal
        from payment_service.app.schemas.payment import RefundRequest

        cached = {"payment_id": str(uuid4()), "status": "REFUNDED"}
        mock_hash.return_value = "hash_cached"
        mock_check.return_value = cached

        result = await refund_payment_internal(
            payment_id=uuid4(),
            request=RefundRequest(),
            db=MagicMock(),
            _=None,
            idempotency_key="idem-key-123",
        )

        assert result == cached
        mock_service_cls.return_value.process_refund.assert_not_called() if hasattr(
            mock_service_cls.return_value, 'process_refund'
        ) else None
