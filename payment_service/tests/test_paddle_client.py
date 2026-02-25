"""Tests for PaddleClient -- webhook signature verification, checkout creation,
subscription management, and HTTP error handling."""

from __future__ import annotations

import hashlib
import hmac
import json

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from payment_service.app.clients.paddle_client import PaddleClientError


# ======================================================================
# Webhook signature verification
# ======================================================================


class TestVerifyWebhookSignature:
    """Tests for Paddle HMAC-SHA256 webhook signature verification."""

    def _sign(self, body: bytes, secret: str, ts: str = "1234567890") -> str:
        """Helper: produce a valid Paddle-Signature header value."""
        signed_payload = f"{ts}:{body.decode('utf-8')}"
        h1 = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"ts={ts};h1={h1}"

    # -- happy path -------------------------------------------------------

    def test_valid_signature_returns_true(self, paddle_client):
        """A correctly signed body must pass verification."""
        raw_body = b'{"event_id":"evt_123","event_type":"subscription.activated"}'
        signature = self._sign(raw_body, "test_webhook_secret")

        assert paddle_client.verify_webhook_signature(raw_body, signature) is True

    def test_valid_signature_with_complex_payload(self, paddle_client):
        """Signatures for larger JSON payloads must also verify."""
        payload = {
            "event_id": "evt_complex",
            "event_type": "transaction.completed",
            "occurred_at": "2026-02-01T10:00:00Z",
            "data": {
                "id": "txn_abc",
                "customer_id": "ctm_xyz",
                "items": [{"price_id": "pri_1", "quantity": 1}],
            },
        }
        raw_body = json.dumps(payload).encode("utf-8")
        signature = self._sign(raw_body, "test_webhook_secret")

        assert paddle_client.verify_webhook_signature(raw_body, signature) is True

    # -- invalid signatures ------------------------------------------------

    def test_invalid_signature_returns_false(self, paddle_client):
        """A forged h1 value must be rejected."""
        raw_body = b'{"event_id":"evt_123"}'
        signature = "ts=1234567890;h1=00000000deadbeef00000000deadbeef00000000deadbeef00000000deadbeef"

        assert paddle_client.verify_webhook_signature(raw_body, signature) is False

    def test_tampered_body_fails(self, paddle_client):
        """Modifying the body after signing must fail verification."""
        original_body = b'{"event_id":"evt_123"}'
        signature = self._sign(original_body, "test_webhook_secret")

        tampered_body = b'{"event_id":"evt_456"}'
        assert paddle_client.verify_webhook_signature(tampered_body, signature) is False

    def test_wrong_secret_fails(self, paddle_client):
        """A signature produced with a different secret must be rejected."""
        raw_body = b'{"event_id":"evt_123"}'
        signature = self._sign(raw_body, "wrong_secret")

        assert paddle_client.verify_webhook_signature(raw_body, signature) is False

    # -- malformed headers -------------------------------------------------

    def test_missing_ts_returns_false(self, paddle_client):
        """Missing ts component must return False."""
        assert paddle_client.verify_webhook_signature(b"body", "h1=abc123") is False

    def test_missing_h1_returns_false(self, paddle_client):
        """Missing h1 component must return False."""
        assert paddle_client.verify_webhook_signature(b"body", "ts=1234567890") is False

    def test_empty_signature_returns_false(self, paddle_client):
        """Empty signature string must return False."""
        assert paddle_client.verify_webhook_signature(b"body", "") is False

    def test_completely_garbage_signature(self, paddle_client):
        """Random string without semicolons must return False."""
        assert paddle_client.verify_webhook_signature(b"body", "not-a-valid-header") is False

    def test_empty_ts_value_returns_false(self, paddle_client):
        """ts= with empty value must return False."""
        assert paddle_client.verify_webhook_signature(b"body", "ts=;h1=abc") is False

    def test_empty_h1_value_returns_false(self, paddle_client):
        """h1= with empty value must return False."""
        assert paddle_client.verify_webhook_signature(b"body", "ts=123;h1=") is False


# ======================================================================
# Checkout session creation
# ======================================================================


class TestCreateCheckoutSession:
    """Tests for PaddleClient.create_checkout_session."""

    @pytest.mark.asyncio
    async def test_returns_checkout_url_and_transaction_id(self, paddle_client):
        """Successful response must return checkout_url and transaction_id."""
        paddle_api_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "id": "txn_test_123",
                    "checkout": {"url": "https://checkout.paddle.com/test"},
                },
            },
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=paddle_api_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await paddle_client.create_checkout_session(
                customer_email="test@example.com",
                price_id="pri_test_123",
                success_url="http://localhost:3000/payment/return",
                custom_data={"user_id": "user_1", "plan_code": "professional"},
            )

        assert result["checkout_url"] == "https://checkout.paddle.com/test"
        assert result["transaction_id"] == "txn_test_123"

    @pytest.mark.asyncio
    async def test_sends_customer_id_when_provided(self, paddle_client):
        """When customer_id is provided it must appear in the POST payload."""
        paddle_api_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "id": "txn_test_456",
                    "checkout": {"url": "https://checkout.paddle.com/existing"},
                },
            },
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=paddle_api_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await paddle_client.create_checkout_session(
                customer_email="test@example.com",
                price_id="pri_test_123",
                success_url="http://localhost:3000/payment/return",
                custom_data={"user_id": "user_1"},
                customer_id="ctm_existing_999",
            )

            # Verify the POST payload included customer_id
            call_kwargs = mock_client.post.call_args
            sent_payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert sent_payload["customer_id"] == "ctm_existing_999"
            assert "customer" not in sent_payload

    @pytest.mark.asyncio
    async def test_sends_customer_email_when_no_customer_id(self, paddle_client):
        """When customer_id is absent, customer.email must be in the payload."""
        paddle_api_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "id": "txn_test_789",
                    "checkout": {"url": "https://checkout.paddle.com/new"},
                },
            },
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=paddle_api_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await paddle_client.create_checkout_session(
                customer_email="new@example.com",
                price_id="pri_test_123",
                success_url="http://localhost:3000/payment/return",
                custom_data={"user_id": "user_2"},
            )

            call_kwargs = mock_client.post.call_args
            sent_payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert sent_payload["customer"]["email"] == "new@example.com"
            assert "customer_id" not in sent_payload

    @pytest.mark.asyncio
    async def test_api_error_raises_paddle_client_error(self, paddle_client):
        """Non-2xx Paddle response must raise PaddleClientError."""
        error_response = httpx.Response(
            status_code=422,
            json={
                "error": {
                    "type": "request_error",
                    "code": "invalid_field",
                    "detail": "price_id is invalid",
                },
            },
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=error_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(PaddleClientError) as exc_info:
                await paddle_client.create_checkout_session(
                    customer_email="test@example.com",
                    price_id="pri_invalid",
                    success_url="http://localhost:3000/payment/return",
                    custom_data={},
                )

            assert exc_info.value.status_code == 422
            assert "price_id is invalid" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_network_error_raises_paddle_client_error(self, paddle_client):
        """Network failure must raise PaddleClientError."""
        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(PaddleClientError, match="Paddle API request failed"):
                await paddle_client.create_checkout_session(
                    customer_email="test@example.com",
                    price_id="pri_test_123",
                    success_url="http://localhost:3000/payment/return",
                    custom_data={},
                )


# ======================================================================
# Subscription management
# ======================================================================


class TestUpdateSubscription:
    """Tests for PaddleClient.update_subscription (plan change)."""

    @pytest.mark.asyncio
    async def test_update_returns_subscription_data(self, paddle_client):
        """Successful update must return the updated subscription object."""
        paddle_api_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "id": "sub_test_1",
                    "status": "active",
                    "items": [{"price": {"id": "pri_new_plan"}, "quantity": 1}],
                },
            },
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.patch = AsyncMock(return_value=paddle_api_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await paddle_client.update_subscription("sub_test_1", "pri_new_plan")

        assert result["id"] == "sub_test_1"
        assert result["status"] == "active"
        assert result["items"][0]["price"]["id"] == "pri_new_plan"

    @pytest.mark.asyncio
    async def test_update_sends_correct_payload(self, paddle_client):
        """PATCH payload must include items and proration_billing_mode."""
        paddle_api_response = httpx.Response(
            status_code=200,
            json={"data": {"id": "sub_test_1", "status": "active", "items": []}},
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.patch = AsyncMock(return_value=paddle_api_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await paddle_client.update_subscription(
                "sub_test_1", "pri_enterprise", proration_billing_mode="prorated_immediately",
            )

            call_kwargs = mock_client.patch.call_args
            sent_payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert sent_payload["items"] == [{"price_id": "pri_enterprise", "quantity": 1}]
            assert sent_payload["proration_billing_mode"] == "prorated_immediately"

    @pytest.mark.asyncio
    async def test_update_uses_patch_method(self, paddle_client):
        """update_subscription must use HTTP PATCH, not POST."""
        paddle_api_response = httpx.Response(
            status_code=200,
            json={"data": {"id": "sub_test_1", "status": "active", "items": []}},
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.patch = AsyncMock(return_value=paddle_api_response)
            mock_client.post = AsyncMock()
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await paddle_client.update_subscription("sub_test_1", "pri_new")

            mock_client.patch.assert_called_once()
            mock_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_calls_correct_endpoint(self, paddle_client):
        """PATCH URL must target /subscriptions/{subscription_id}."""
        paddle_api_response = httpx.Response(
            status_code=200,
            json={"data": {"id": "sub_test_42", "status": "active", "items": []}},
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.patch = AsyncMock(return_value=paddle_api_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await paddle_client.update_subscription("sub_test_42", "pri_new")

            call_args = mock_client.patch.call_args
            url = call_args.args[0] if call_args.args else call_args.kwargs.get("url", "")
            assert "subscriptions/sub_test_42" in str(url)

    @pytest.mark.asyncio
    async def test_update_api_error_raises_paddle_client_error(self, paddle_client):
        """Non-2xx response from Paddle must raise PaddleClientError."""
        error_response = httpx.Response(
            status_code=409,
            json={
                "error": {
                    "type": "request_error",
                    "code": "subscription_update_conflict",
                    "detail": "Subscription has a pending change",
                },
            },
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.patch = AsyncMock(return_value=error_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(PaddleClientError) as exc_info:
                await paddle_client.update_subscription("sub_test_1", "pri_bad")

            assert exc_info.value.status_code == 409
            assert "pending change" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_network_error_raises_paddle_client_error(self, paddle_client):
        """Network failure during update must raise PaddleClientError."""
        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.patch = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(PaddleClientError, match="Paddle API request failed"):
                await paddle_client.update_subscription("sub_test_1", "pri_test")


class TestCancelSubscription:
    """Tests for PaddleClient.cancel_subscription."""

    @pytest.mark.asyncio
    async def test_cancel_returns_subscription_data(self, paddle_client):
        """Successful cancellation must return the subscription object."""
        paddle_api_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "id": "sub_test_1",
                    "status": "canceled",
                    "scheduled_change": {
                        "action": "cancel",
                        "effective_at": "2026-03-01T00:00:00Z",
                    },
                },
            },
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=paddle_api_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await paddle_client.cancel_subscription("sub_test_1")

        assert result["id"] == "sub_test_1"
        assert result["status"] == "canceled"

    @pytest.mark.asyncio
    async def test_cancel_sends_effective_from_immediately(self, paddle_client):
        """effective_from='immediately' must appear in the POST payload."""
        paddle_api_response = httpx.Response(
            status_code=200,
            json={"data": {"id": "sub_test_2", "status": "canceled"}},
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=paddle_api_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            await paddle_client.cancel_subscription("sub_test_2", effective_from="immediately")

            call_kwargs = mock_client.post.call_args
            sent_payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert sent_payload["effective_from"] == "immediately"


# ======================================================================
# GET helpers (subscription / transaction details)
# ======================================================================


class TestGetSubscription:
    """Tests for PaddleClient.get_subscription."""

    @pytest.mark.asyncio
    async def test_returns_subscription_object(self, paddle_client):
        """GET /subscriptions/{id} must return parsed data."""
        paddle_api_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "id": "sub_test_1",
                    "status": "active",
                    "customer_id": "ctm_test_1",
                },
            },
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=paddle_api_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await paddle_client.get_subscription("sub_test_1")

        assert result["id"] == "sub_test_1"
        assert result["status"] == "active"


class TestGetTransaction:
    """Tests for PaddleClient.get_transaction."""

    @pytest.mark.asyncio
    async def test_returns_transaction_object(self, paddle_client):
        """GET /transactions/{id} must return parsed data."""
        paddle_api_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "id": "txn_test_1",
                    "status": "completed",
                    "customer_id": "ctm_test_1",
                },
            },
        )

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=paddle_api_response)
            MockAsyncClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockAsyncClient.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await paddle_client.get_transaction("txn_test_1")

        assert result["id"] == "txn_test_1"
        assert result["status"] == "completed"


# ======================================================================
# _handle_response edge cases
# ======================================================================


class TestHandleResponse:
    """Tests for the static _handle_response helper."""

    def test_success_returns_data_envelope(self, paddle_client):
        """2xx response must extract the 'data' key."""
        response = httpx.Response(
            status_code=200,
            json={"data": {"id": "test_1"}},
        )

        from payment_service.app.clients.paddle_client import PaddleClient
        result = PaddleClient._handle_response(response)
        assert result == {"id": "test_1"}

    def test_success_missing_data_key_returns_empty_dict(self, paddle_client):
        """2xx response without 'data' key must return empty dict."""
        response = httpx.Response(
            status_code=200,
            json={"meta": {"request_id": "abc"}},
        )

        from payment_service.app.clients.paddle_client import PaddleClient
        result = PaddleClient._handle_response(response)
        assert result == {}

    def test_error_response_raises_with_detail(self, paddle_client):
        """Non-2xx response must raise PaddleClientError with error detail."""
        response = httpx.Response(
            status_code=400,
            json={
                "error": {
                    "type": "request_error",
                    "code": "bad_request",
                    "detail": "Invalid request body",
                },
            },
        )

        from payment_service.app.clients.paddle_client import PaddleClient
        with pytest.raises(PaddleClientError) as exc_info:
            PaddleClient._handle_response(response)

        assert exc_info.value.status_code == 400
        assert exc_info.value.response_body is not None
        assert "Invalid request body" in str(exc_info.value)

    def test_error_response_non_json_body(self, paddle_client):
        """Non-2xx response with non-JSON body must still raise."""
        response = httpx.Response(
            status_code=500,
            text="Internal Server Error",
        )

        from payment_service.app.clients.paddle_client import PaddleClient
        with pytest.raises(PaddleClientError) as exc_info:
            PaddleClient._handle_response(response)

        assert exc_info.value.status_code == 500


# ======================================================================
# Client initialisation
# ======================================================================


class TestClientInitialisation:
    """Tests for PaddleClient constructor behaviour."""

    def test_sandbox_environment_uses_sandbox_url(self, paddle_client):
        """Sandbox environment must use the sandbox base URL."""
        assert "sandbox" in paddle_client.base_url

    def test_production_environment_uses_production_url(self):
        """Production environment must use the production base URL."""
        with patch("payment_service.app.clients.paddle_client.settings") as mock_settings:
            mock_settings.paddle_api_key = "live_key"
            mock_settings.paddle_webhook_secret = "live_secret"
            mock_settings.paddle_environment = "production"

            from payment_service.app.clients.paddle_client import PaddleClient
            client = PaddleClient()

        assert client.base_url == "https://api.paddle.com"

    def test_build_headers_contains_bearer_token(self, paddle_client):
        """Authorization header must include the API key as Bearer token."""
        headers = paddle_client._build_headers()
        assert headers["Authorization"] == "Bearer test_api_key"
        assert headers["Content-Type"] == "application/json"
