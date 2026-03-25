"""Tests for SubscriptionClient and PaymentClient.

All HTTP calls are intercepted via httpx mocking — no real network
traffic occurs.
"""
from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest

from app.clients.subscription_client import SubscriptionClient
from app.clients.payment_client import PaymentClient


# ---------------------------------------------------------------------------
# SubscriptionClient
# ---------------------------------------------------------------------------

class TestSubscriptionClientGetExpiring:
    @pytest.mark.asyncio
    async def test_returns_subscriptions(self):
        client = SubscriptionClient()
        expected = [{"id": 1, "user_id": "u1"}, {"id": 2, "user_id": "u2"}]

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = expected
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            result = await client.get_expiring_subscriptions(days_ahead=2)

        assert result == expected
        mock_client_instance.get.assert_called_once()
        call_kwargs = mock_client_instance.get.call_args
        assert "days_ahead" in call_kwargs.kwargs.get("params", {}) or \
               "days_ahead" in (call_kwargs[1].get("params", {}) if len(call_kwargs) > 1 else {})

    @pytest.mark.asyncio
    async def test_raises_on_http_error(self):
        client = SubscriptionClient()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=mock_response,
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            with pytest.raises(httpx.HTTPStatusError):
                await client.get_expiring_subscriptions()

    @pytest.mark.asyncio
    async def test_headers_include_internal_token(self):
        client = SubscriptionClient()
        headers = client._get_headers()

        assert "X-Internal-Token" in headers
        assert headers["Content-Type"] == "application/json"


class TestSubscriptionClientExtend:
    @pytest.mark.asyncio
    async def test_posts_to_extend_endpoint(self):
        client = SubscriptionClient()
        expected = {"status": "extended", "expires_at": "2026-04-25"}

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = expected
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            result = await client.extend_subscription(
                subscription_id=42, payment_id="pay-123"
            )

        assert result == expected
        call_args = mock_client_instance.post.call_args
        assert "/42:extend" in call_args[0][0] or "/42:extend" in call_args.args[0]

    @pytest.mark.asyncio
    async def test_extend_raises_on_error(self):
        client = SubscriptionClient()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            with pytest.raises(httpx.HTTPStatusError):
                await client.extend_subscription(
                    subscription_id=999, payment_id="p"
                )


class TestSubscriptionClientMarkPastDue:
    @pytest.mark.asyncio
    async def test_posts_to_mark_past_due_endpoint(self):
        client = SubscriptionClient()
        expected = {"status": "past_due"}

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = expected
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            result = await client.mark_subscription_past_due(
                subscription_id=42, reason="payment_declined"
            )

        assert result == expected
        call_args = mock_client_instance.post.call_args
        url = call_args[0][0] if call_args[0] else call_args.args[0]
        assert ":mark_past_due" in url

    @pytest.mark.asyncio
    async def test_mark_past_due_sends_reason_in_body(self):
        client = SubscriptionClient()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            await client.mark_subscription_past_due(
                subscription_id=42, reason="insufficient_funds"
            )

        call_kwargs = mock_client_instance.post.call_args.kwargs
        assert call_kwargs["json"]["reason"] == "insufficient_funds"


# ---------------------------------------------------------------------------
# PaymentClient
# ---------------------------------------------------------------------------

class TestPaymentClientCreateRecurring:
    @pytest.mark.asyncio
    async def test_creates_payment_with_correct_payload(self):
        client = PaymentClient()
        expected = {"payment_id": "pay-abc", "status": "PAID"}

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = expected
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            result = await client.create_recurring_payment(
                user_id="user-1",
                subscription_id=42,
                plan_code="pro_monthly",
                amount=Decimal("199.00"),
                currency="UAH",
                recurring_token="tok_abc",
            )

        assert result == expected
        call_kwargs = mock_client_instance.post.call_args.kwargs
        payload = call_kwargs["json"]
        assert payload["user_id"] == "user-1"
        assert payload["subscription_id"] == 42
        assert payload["plan_code"] == "pro_monthly"
        assert payload["amount"] == "199.00"
        assert payload["currency"] == "UAH"
        assert payload["recurring_token"] == "tok_abc"

    @pytest.mark.asyncio
    async def test_includes_idempotency_key(self):
        client = PaymentClient()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {"payment_id": "p1", "status": "PAID"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            await client.create_recurring_payment(
                user_id="u",
                subscription_id=42,
                plan_code="pro",
                amount=Decimal("100"),
                currency="UAH",
                recurring_token="tok",
            )

        call_kwargs = mock_client_instance.post.call_args.kwargs
        headers = call_kwargs["headers"]
        assert "Idempotency-Key" in headers
        assert len(headers["Idempotency-Key"]) == 64  # SHA-256 hex

    @pytest.mark.asyncio
    async def test_idempotency_key_is_deterministic(self):
        """Same subscription + same day = same key."""
        client = PaymentClient()
        sub_id = 42
        expected_key = hashlib.sha256(
            f"renewal_{sub_id}_{date.today().isoformat()}".encode()
        ).hexdigest()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {"payment_id": "p1", "status": "PAID"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            await client.create_recurring_payment(
                user_id="u",
                subscription_id=sub_id,
                plan_code="pro",
                amount=Decimal("100"),
                currency="UAH",
                recurring_token="tok",
            )

        call_kwargs = mock_client_instance.post.call_args.kwargs
        assert call_kwargs["headers"]["Idempotency-Key"] == expected_key

    @pytest.mark.asyncio
    async def test_raises_on_http_error(self):
        client = PaymentClient()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "502", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            with pytest.raises(httpx.HTTPStatusError):
                await client.create_recurring_payment(
                    user_id="u",
                    subscription_id=1,
                    plan_code="p",
                    amount=Decimal("100"),
                    currency="UAH",
                    recurring_token="tok",
                )

    @pytest.mark.asyncio
    async def test_posts_to_recurring_endpoint(self):
        client = PaymentClient()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {"payment_id": "p", "status": "PAID"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            await client.create_recurring_payment(
                user_id="u",
                subscription_id=1,
                plan_code="p",
                amount=Decimal("10"),
                currency="USD",
                recurring_token="t",
            )

        url = mock_client_instance.post.call_args[0][0]
        assert url.endswith("/v1/internal/payments:recurring")


class TestPaymentClientGetPaymentStatus:
    @pytest.mark.asyncio
    async def test_returns_status(self):
        client = PaymentClient()
        expected = {"status": "PAID", "amount": "100.00"}

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = expected
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            result = await client.get_payment_status("pay-123")

        assert result == expected
        url = mock_client_instance.get.call_args[0][0]
        assert "pay-123" in url

    @pytest.mark.asyncio
    async def test_raises_on_not_found(self):
        client = PaymentClient()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockAsyncClient.return_value = mock_client_instance

            with pytest.raises(httpx.HTTPStatusError):
                await client.get_payment_status("nonexistent")
