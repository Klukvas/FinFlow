"""Tests for the payments router endpoints.

Tests get_payment_status, check_paddle_config, create_payment,
change_plan, get_payment_by_order_reference, get_payment, list_payments.
"""

from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from payment_service.app.models.models import (
    Payment,
    PaymentStatus,
    PaymentProvider,
    PaymentPurpose,
)
from payment_service.app.utils.errors import AuthError, ValidationError
from payment_service.app.utils.jwt import JWTPayload


# ======================================================================
# get_payment_status
# ======================================================================


class TestGetPaymentStatus:
    """Tests for the /config/status endpoint."""

    @patch("payment_service.app.routers.payments.settings")
    def test_returns_status(self, mock_settings):
        from payment_service.app.routers.payments import get_payment_status

        mock_settings.payments_enabled = True

        result = get_payment_status()

        assert result["payments_enabled"] is True
        assert result["service_status"] == "operational"

    @patch("payment_service.app.routers.payments.settings")
    def test_returns_disabled_status(self, mock_settings):
        from payment_service.app.routers.payments import get_payment_status

        mock_settings.payments_enabled = False

        result = get_payment_status()
        assert result["payments_enabled"] is False


# ======================================================================
# check_paddle_config
# ======================================================================


class TestCheckPaddleConfig:
    """Tests for the /config/check endpoint."""

    @patch("payment_service.app.routers.payments.settings")
    def test_configured_returns_ok(self, mock_settings):
        from payment_service.app.routers.payments import check_paddle_config

        mock_settings.paddle_api_key = "test_key"
        mock_settings.paddle_webhook_secret = "test_secret"
        mock_settings.paddle_environment = "production"
        mock_settings.paddle_success_url = "https://example.com/return"

        result = check_paddle_config()

        assert result["status"] == "ok"
        assert result["production_ready"] is True
        assert result["checks"]["api_key"]["configured"] is True
        assert result["checks"]["webhook_secret"]["configured"] is True

    @patch("payment_service.app.routers.payments.settings")
    def test_not_configured_returns_configuration_needed(self, mock_settings):
        from payment_service.app.routers.payments import check_paddle_config

        mock_settings.paddle_api_key = ""
        mock_settings.paddle_webhook_secret = ""
        mock_settings.paddle_environment = "sandbox"
        mock_settings.paddle_success_url = ""

        result = check_paddle_config()

        assert result["status"] == "configuration_needed"
        assert result["production_ready"] is False

    @patch("payment_service.app.routers.payments.settings")
    def test_sandbox_not_production_ready(self, mock_settings):
        from payment_service.app.routers.payments import check_paddle_config

        mock_settings.paddle_api_key = "key"
        mock_settings.paddle_webhook_secret = "secret"
        mock_settings.paddle_environment = "sandbox"
        mock_settings.paddle_success_url = "url"

        result = check_paddle_config()
        assert result["production_ready"] is False


# ======================================================================
# create_payment
# ======================================================================


class TestCreatePaymentEndpoint:
    """Tests for the POST /payments endpoint."""

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.payments.settings")
    async def test_payments_disabled_raises_validation_error(self, mock_settings):
        from payment_service.app.routers.payments import create_payment
        from payment_service.app.schemas.payment import CreatePaymentRequest

        mock_settings.payments_enabled = False

        request = CreatePaymentRequest(
            user_id="u1",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="pro",
            amount=Decimal("10.00"),
            currency="USD",
        )
        user = JWTPayload(user_id="u1", email="t@t.com")

        with pytest.raises(ValidationError) as exc_info:
            await create_payment(
                request=request,
                db=MagicMock(),
                current_user=user,
                idempotency_key=None,
                _rate_limit=None,
            )
        assert "PAYMENTS_DISABLED" in exc_info.value.error_code

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.payments.settings")
    async def test_user_mismatch_raises_auth_error(self, mock_settings):
        from payment_service.app.routers.payments import create_payment
        from payment_service.app.schemas.payment import CreatePaymentRequest

        mock_settings.payments_enabled = True

        request = CreatePaymentRequest(
            user_id="user_A",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="pro",
            amount=Decimal("10.00"),
            currency="USD",
        )
        user = JWTPayload(user_id="user_B", email="t@t.com")

        with pytest.raises(AuthError) as exc_info:
            await create_payment(
                request=request,
                db=MagicMock(),
                current_user=user,
                idempotency_key=None,
                _rate_limit=None,
            )
        assert "UNAUTHORIZED_USER" in exc_info.value.error_code

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.payments.PaymentService")
    @patch("payment_service.app.routers.payments.settings")
    async def test_successful_creation(self, mock_settings, mock_service_cls):
        from payment_service.app.routers.payments import create_payment
        from payment_service.app.schemas.payment import CreatePaymentRequest

        mock_settings.payments_enabled = True

        payment_id = uuid4()
        mock_payment = MagicMock(spec=Payment)
        mock_payment.id = payment_id
        mock_payment.order_reference = "ORDER_api_1"
        mock_payment.provider = PaymentProvider.PADDLE
        mock_payment.amount = Decimal("29.99")
        mock_payment.currency = "USD"
        mock_payment.status = PaymentStatus.CREATED
        mock_payment.provider_payment_url = "https://checkout.paddle.com/test"
        mock_payment.paddle_transaction_id = "txn_api_1"
        mock_payment.provider_payload = None
        mock_payment.created_at = datetime.utcnow()

        mock_service = MagicMock()
        mock_service.create_payment = AsyncMock(return_value=mock_payment)
        mock_service_cls.return_value = mock_service

        request = CreatePaymentRequest(
            user_id="u1",
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code="pro",
            amount=Decimal("29.99"),
            currency="USD",
        )
        user = JWTPayload(user_id="u1", email="t@t.com")

        result = await create_payment(
            request=request,
            db=MagicMock(),
            current_user=user,
            idempotency_key=None,
            _rate_limit=None,
        )

        assert result.payment_id == payment_id
        assert result.checkout_url == "https://checkout.paddle.com/test"


# ======================================================================
# change_plan
# ======================================================================


class TestChangePlanEndpoint:
    """Tests for the POST /payments/change-plan endpoint."""

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.payments.settings")
    async def test_payments_disabled_raises(self, mock_settings):
        from payment_service.app.routers.payments import change_plan
        from payment_service.app.schemas.payment import ChangePlanRequest

        mock_settings.payments_enabled = False

        request = ChangePlanRequest(
            user_id="u1",
            new_plan_code="enterprise",
            paddle_subscription_id="sub_1",
        )
        user = JWTPayload(user_id="u1", email="t@t.com")

        with pytest.raises(ValidationError) as exc_info:
            await change_plan(request=request, db=MagicMock(), current_user=user)
        assert "PAYMENTS_DISABLED" in exc_info.value.error_code

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.payments.settings")
    async def test_user_mismatch_raises_auth_error(self, mock_settings):
        from payment_service.app.routers.payments import change_plan
        from payment_service.app.schemas.payment import ChangePlanRequest

        mock_settings.payments_enabled = True

        request = ChangePlanRequest(
            user_id="user_owner",
            new_plan_code="enterprise",
            paddle_subscription_id="sub_1",
        )
        user = JWTPayload(user_id="user_other", email="t@t.com")

        with pytest.raises(AuthError) as exc_info:
            await change_plan(request=request, db=MagicMock(), current_user=user)
        assert "UNAUTHORIZED_USER" in exc_info.value.error_code


# ======================================================================
# get_payment_by_order_reference
# ======================================================================


class TestGetPaymentByOrderReference:
    """Tests for the GET /payments/by-order/{order_reference} endpoint."""

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.payments.PaymentService")
    async def test_returns_payment_for_owner(self, mock_service_cls):
        from payment_service.app.routers.payments import get_payment_by_order_reference

        mock_payment = MagicMock(spec=Payment)
        mock_payment.id = uuid4()
        mock_payment.user_id = "u1"
        mock_payment.provider = PaymentProvider.PADDLE
        mock_payment.order_reference = "ORDER_by_ref"
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
        mock_service.payment_repo.get_by_order_reference_or_raise.return_value = mock_payment
        mock_service_cls.return_value = mock_service

        user = JWTPayload(user_id="u1", email="t@t.com")

        result = await get_payment_by_order_reference(
            order_reference="ORDER_by_ref",
            db=MagicMock(),
            current_user=user,
        )

        assert result.order_reference == "ORDER_by_ref"

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.payments.PaymentService")
    async def test_other_user_raises_auth_error(self, mock_service_cls):
        from payment_service.app.routers.payments import get_payment_by_order_reference

        mock_payment = MagicMock(spec=Payment)
        mock_payment.user_id = "owner_user"

        mock_service = MagicMock()
        mock_service.payment_repo.get_by_order_reference_or_raise.return_value = mock_payment
        mock_service_cls.return_value = mock_service

        user = JWTPayload(user_id="other_user", email="t@t.com")

        with pytest.raises(AuthError) as exc_info:
            await get_payment_by_order_reference(
                order_reference="ORDER_x",
                db=MagicMock(),
                current_user=user,
            )
        assert "UNAUTHORIZED_ACCESS" in exc_info.value.error_code


# ======================================================================
# get_payment
# ======================================================================


class TestGetPayment:
    """Tests for the GET /payments/{payment_id} endpoint."""

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.payments.PaymentService")
    async def test_other_user_raises_auth_error(self, mock_service_cls):
        from payment_service.app.routers.payments import get_payment

        mock_payment = MagicMock(spec=Payment)
        mock_payment.user_id = "owner"

        mock_service = MagicMock()
        mock_service.payment_repo.get_by_id_or_raise.return_value = mock_payment
        mock_service_cls.return_value = mock_service

        user = JWTPayload(user_id="intruder", email="t@t.com")

        with pytest.raises(AuthError) as exc_info:
            await get_payment(
                payment_id=uuid4(),
                db=MagicMock(),
                current_user=user,
            )
        assert "UNAUTHORIZED_ACCESS" in exc_info.value.error_code


# ======================================================================
# list_payments
# ======================================================================


class TestListPaymentsEndpoint:
    """Tests for the GET /payments endpoint."""

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.payments.PaymentService")
    async def test_returns_user_payments(self, mock_service_cls):
        from payment_service.app.routers.payments import list_payments

        p1 = MagicMock(spec=Payment)
        p1.id = uuid4()
        p1.provider = PaymentProvider.PADDLE
        p1.order_reference = "ORDER_list_1"
        p1.user_id = "u1"
        p1.workspace_id = None
        p1.purpose = PaymentPurpose.SUBSCRIPTION
        p1.plan_code = "pro"
        p1.amount = Decimal("10")
        p1.currency = "USD"
        p1.status = PaymentStatus.PAID
        p1.provider_payment_url = None
        p1.paid_at = datetime.utcnow()
        p1.failed_at = None
        p1.refunded_at = None
        p1.failure_reason = None
        p1.extra_data = None
        p1.created_at = datetime.utcnow()
        p1.updated_at = datetime.utcnow()
        p1.events = []

        mock_service = MagicMock()
        mock_service.payment_repo.get_by_user_id.return_value = [p1]
        mock_service_cls.return_value = mock_service

        user = JWTPayload(user_id="u1", email="t@t.com")

        result = await list_payments(
            limit=50,
            offset=0,
            db=MagicMock(),
            current_user=user,
        )

        assert len(result) == 1
        mock_service.payment_repo.get_by_user_id.assert_called_once_with(
            user_id="u1",
            limit=50,
            offset=0,
        )

    @pytest.mark.asyncio
    @patch("payment_service.app.routers.payments.PaymentService")
    async def test_caps_limit_at_100(self, mock_service_cls):
        from payment_service.app.routers.payments import list_payments

        mock_service = MagicMock()
        mock_service.payment_repo.get_by_user_id.return_value = []
        mock_service_cls.return_value = mock_service

        user = JWTPayload(user_id="u1", email="t@t.com")

        await list_payments(
            limit=500,
            offset=0,
            db=MagicMock(),
            current_user=user,
        )

        call_kwargs = mock_service.payment_repo.get_by_user_id.call_args.kwargs
        assert call_kwargs["limit"] == 100
