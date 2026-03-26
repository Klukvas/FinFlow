"""Tests for PaymentService.change_subscription_plan -- upgrade and downgrade
via Paddle PATCH /subscriptions/{id} API."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from payment_service.app.config import PaddlePriceEntry
from payment_service.app.schemas.payment import ChangePlanRequest
from payment_service.app.utils.errors import ValidationError


# ======================================================================
# Helpers
# ======================================================================


def _consent_metadata() -> dict:
    """Valid consent metadata for plan change requests."""
    return {
        "consent_given": True,
        "consent_version": "v1.0.0",
        "consent_timestamp": datetime.now(timezone.utc).isoformat(),
        "consent_language": "en",
    }


# ======================================================================
# change_subscription_plan -- happy path
# ======================================================================


class TestChangePlanHappyPath:
    """Verify the upgrade/downgrade flow through Paddle API update."""

    @pytest.mark.asyncio
    async def test_upgrade_calls_paddle_update(
        self, payment_service, mock_db, mock_paddle_client,
    ):
        """Upgrading professional→enterprise must call paddle_client.update_subscription."""
        # get_subscription returns current sub with old price
        mock_paddle_client.get_subscription = AsyncMock(return_value={
            "id": "sub_existing_1",
            "status": "active",
            "items": [{"price": {"id": "pri_test_pro"}, "quantity": 1}],
        })

        request = ChangePlanRequest(
            user_id="user_1",
            new_plan_code="enterprise",
            paddle_subscription_id="sub_existing_1",
            metadata=_consent_metadata(),
        )

        result = await payment_service.change_subscription_plan(request)

        assert result["success"] is True
        assert result["new_plan_code"] == "enterprise"
        assert result["paddle_subscription_id"] == "sub_existing_1"

        mock_paddle_client.update_subscription.assert_awaited_once_with(
            subscription_id="sub_existing_1",
            new_price_id="pri_test_ent",
        )

    @pytest.mark.asyncio
    async def test_downgrade_calls_paddle_update(
        self, payment_service, mock_db, mock_paddle_client,
    ):
        """Downgrading enterprise→professional must work via the same API path."""
        mock_paddle_client.get_subscription = AsyncMock(return_value={
            "id": "sub_existing_2",
            "status": "active",
            "items": [{"price": {"id": "pri_test_ent"}, "quantity": 1}],
        })

        request = ChangePlanRequest(
            user_id="user_2",
            new_plan_code="professional",
            paddle_subscription_id="sub_existing_2",
            metadata=_consent_metadata(),
        )

        result = await payment_service.change_subscription_plan(request)

        assert result["success"] is True
        assert result["new_plan_code"] == "professional"

        mock_paddle_client.update_subscription.assert_awaited_once_with(
            subscription_id="sub_existing_2",
            new_price_id="pri_test_pro",
        )

    @pytest.mark.asyncio
    async def test_notifies_subscription_service(
        self, payment_service, mock_db, mock_paddle_client,
    ):
        """After a plan change, subscription_service must be notified."""
        request = ChangePlanRequest(
            user_id="user_notify",
            new_plan_code="enterprise",
            paddle_subscription_id="sub_notify_1",
            metadata=_consent_metadata(),
        )

        await payment_service.change_subscription_plan(request)

        payment_service.subscription_client.notify_payment_success.assert_awaited_once()
        call_kwargs = payment_service.subscription_client.notify_payment_success.call_args.kwargs
        assert call_kwargs["user_id"] == "user_notify"
        assert call_kwargs["plan_code"] == "enterprise"
        assert call_kwargs["paddle_subscription_id"] == "sub_notify_1"
        assert call_kwargs["paddle_price_id"] == "pri_test_ent"

    @pytest.mark.asyncio
    async def test_resolves_old_plan_code(
        self, payment_service, mock_db, mock_paddle_client,
    ):
        """The response must include old_plan_code resolved from the old price_id."""
        mock_paddle_client.get_subscription = AsyncMock(return_value={
            "id": "sub_resolve",
            "status": "active",
            "items": [{"price": {"id": "pri_test_pro"}, "quantity": 1}],
        })

        request = ChangePlanRequest(
            user_id="user_resolve",
            new_plan_code="enterprise",
            paddle_subscription_id="sub_resolve",
            metadata=_consent_metadata(),
        )

        result = await payment_service.change_subscription_plan(request)

        assert result["old_plan_code"] == "professional"
        assert result["new_plan_code"] == "enterprise"


# ======================================================================
# change_subscription_plan -- validation errors
# ======================================================================


class TestChangePlanValidation:
    """Verify validation: consent, price mapping, etc."""

    @pytest.mark.asyncio
    async def test_missing_consent_raises(self, payment_service, mock_db):
        """Plan change without consent metadata must raise ValidationError."""
        request = ChangePlanRequest(
            user_id="user_no_consent",
            new_plan_code="enterprise",
            paddle_subscription_id="sub_no_consent",
            metadata=None,
        )

        with pytest.raises(ValidationError) as exc_info:
            await payment_service.change_subscription_plan(request)

        assert "METADATA_REQUIRED" in exc_info.value.error_code

    @pytest.mark.asyncio
    async def test_consent_not_given_raises(self, payment_service, mock_db):
        """Plan change with consent_given=False must raise ValidationError."""
        request = ChangePlanRequest(
            user_id="user_no_consent_flag",
            new_plan_code="enterprise",
            paddle_subscription_id="sub_1",
            metadata={
                "consent_given": False,
                "consent_version": "v1.0.0",
                "consent_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            await payment_service.change_subscription_plan(request)

        assert "CONSENT_REQUIRED" in exc_info.value.error_code

    @pytest.mark.asyncio
    async def test_missing_price_mapping_raises(self, payment_service, mock_db):
        """Plan change to an unconfigured plan must raise."""
        request = ChangePlanRequest(
            user_id="user_no_price",
            new_plan_code="nonexistent_plan",
            paddle_subscription_id="sub_1",
            metadata=_consent_metadata(),
        )

        with pytest.raises(ValidationError) as exc_info:
            await payment_service.change_subscription_plan(request)

        assert "PRICE_NOT_CONFIGURED" in exc_info.value.error_code

    @pytest.mark.asyncio
    async def test_wrong_consent_version_raises(self, payment_service, mock_db):
        """Plan change with outdated consent version must raise."""
        request = ChangePlanRequest(
            user_id="user_old_consent",
            new_plan_code="enterprise",
            paddle_subscription_id="sub_1",
            metadata={
                "consent_given": True,
                "consent_version": "v0.1.0",  # outdated
                "consent_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        with pytest.raises(ValidationError) as exc_info:
            await payment_service.change_subscription_plan(request)

        assert "CONSENT_VERSION_MISMATCH" in exc_info.value.error_code


# ======================================================================
# change_subscription_plan -- Paddle API failure
# ======================================================================


class TestChangePlanApiFailure:
    """Verify that Paddle API errors propagate correctly."""

    @pytest.mark.asyncio
    async def test_paddle_api_error_propagates(
        self, payment_service, mock_db, mock_paddle_client,
    ):
        """When Paddle returns an error, the exception must propagate."""
        from payment_service.app.clients.paddle_client import PaddleClientError

        mock_paddle_client.update_subscription = AsyncMock(
            side_effect=PaddleClientError("Subscription not found", status_code=404),
        )

        request = ChangePlanRequest(
            user_id="user_api_fail",
            new_plan_code="enterprise",
            paddle_subscription_id="sub_nonexistent",
            metadata=_consent_metadata(),
        )

        with pytest.raises(PaddleClientError):
            await payment_service.change_subscription_plan(request)

        # subscription_service should NOT have been notified
        payment_service.subscription_client.notify_payment_success.assert_not_awaited()
