"""Paddle Billing API client.

Handles all communication with the Paddle API including:
- Creating checkout sessions (transactions)
- Verifying webhook signatures
- Cancelling subscriptions
- Fetching subscription and transaction details
"""
from __future__ import annotations

import hashlib
import hmac as hmac_module
import logging
from typing import Any, Optional

import httpx

from ..config import settings

logger = logging.getLogger("payment_service.paddle_client")

SANDBOX_BASE_URL = "https://sandbox-api.paddle.com"
PRODUCTION_BASE_URL = "https://api.paddle.com"

# HTTP timeout for Paddle API calls (seconds)
DEFAULT_TIMEOUT = 30.0


class PaddleClientError(Exception):
    """Raised when a Paddle API call fails."""

    def __init__(self, message: str, status_code: int | None = None, response_body: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class PaddleClient:
    """Client for the Paddle Billing API.

    Reads configuration from application settings on init.
    All HTTP calls are async via httpx.
    """

    def __init__(self) -> None:
        self.api_key: str = settings.paddle_api_key
        self.webhook_secret: str = settings.paddle_webhook_secret

        if settings.paddle_environment == "production":
            self.base_url = PRODUCTION_BASE_URL
        else:
            self.base_url = SANDBOX_BASE_URL

        self._validate_configuration()

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def _validate_configuration(self) -> None:
        """Log warnings when critical settings are missing."""
        if not self.api_key:
            logger.warning("PADDLE_API_KEY is not configured")
        if not self.webhook_secret:
            logger.warning("PADDLE_WEBHOOK_SECRET is not configured")

        logger.info(
            "Paddle client initialized",
            extra={
                "environment": settings.paddle_environment,
                "base_url": self.base_url,
                "has_api_key": bool(self.api_key),
                "has_webhook_secret": bool(self.webhook_secret),
            },
        )

    def _build_headers(self) -> dict[str, str]:
        """Return standard authorization headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Checkout / Transactions
    # ------------------------------------------------------------------

    async def create_checkout_session(
        self,
        customer_email: str,
        price_id: str,
        success_url: str,
        custom_data: dict[str, str],
        customer_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a Paddle checkout session via ``POST /transactions``.

        If *customer_id* is provided the transaction is attached to an
        existing Paddle customer; otherwise a new customer record is
        created from *customer_email*.

        Returns:
            ``{"checkout_url": "...", "transaction_id": "txn_..."}``

        Raises:
            PaddleClientError: on non-2xx response or network failure.
        """
        url = f"{self.base_url}/transactions"
        payload: dict[str, Any] = {
            "items": [{"price_id": price_id, "quantity": 1}],
            "custom_data": custom_data,
            "checkout": {
                "settings": {
                    "success_url": success_url,
                },
            },
        }

        if customer_id:
            payload["customer_id"] = customer_id
        elif customer_email:
            payload["customer"] = {"email": customer_email}

        logger.info(
            "Creating Paddle checkout session",
            extra={
                "price_id": price_id,
                "customer_email": customer_email,
                "has_customer_id": bool(customer_id),
            },
        )

        data = await self._post(url, payload)
        checkout_url = data.get("checkout", {}).get("url", "")
        transaction_id = data.get("id", "")

        logger.info(
            "Paddle checkout session created",
            extra={
                "transaction_id": transaction_id,
                "has_checkout_url": bool(checkout_url),
            },
        )

        return {
            "checkout_url": checkout_url,
            "transaction_id": transaction_id,
        }

    # ------------------------------------------------------------------
    # Webhook signature verification
    # ------------------------------------------------------------------

    def verify_webhook_signature(self, raw_body: bytes, paddle_signature: str) -> bool:
        """Verify a Paddle webhook signature (HMAC-SHA256).

        Paddle sends a header ``Paddle-Signature`` containing::

            ts=<timestamp>;h1=<hmac_hex>

        The signed payload is ``"<ts>:<raw_body>"`` using the webhook
        secret as key.

        Returns:
            ``True`` if the signature is valid.
        """
        parts: dict[str, str] = {}
        for segment in paddle_signature.split(";"):
            key, _, value = segment.partition("=")
            parts[key.strip()] = value.strip()

        ts = parts.get("ts", "")
        h1 = parts.get("h1", "")

        if not ts or not h1:
            logger.warning(
                "Paddle webhook signature missing ts or h1",
                extra={"raw_header": paddle_signature[:120]},
            )
            return False

        signed_payload = f"{ts}:{raw_body.decode('utf-8')}"
        expected = hmac_module.new(
            self.webhook_secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        is_valid = hmac_module.compare_digest(expected, h1)

        if not is_valid:
            logger.warning(
                "Paddle webhook signature mismatch",
                extra={"ts": ts},
            )

        return is_valid

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------

    async def cancel_subscription(
        self,
        subscription_id: str,
        effective_from: str = "next_billing_period",
    ) -> dict[str, Any]:
        """Cancel a Paddle subscription.

        Args:
            subscription_id: The Paddle subscription ID (``sub_...``).
            effective_from: ``"next_billing_period"`` or ``"immediately"``.

        Returns:
            The subscription object returned by Paddle.

        Raises:
            PaddleClientError: on non-2xx response or network failure.
        """
        url = f"{self.base_url}/subscriptions/{subscription_id}/cancel"
        payload = {"effective_from": effective_from}

        logger.info(
            "Cancelling Paddle subscription",
            extra={
                "subscription_id": subscription_id,
                "effective_from": effective_from,
            },
        )

        data = await self._post(url, payload)

        logger.info(
            "Paddle subscription cancelled",
            extra={
                "subscription_id": subscription_id,
                "status": data.get("status"),
            },
        )

        return data

    async def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Fetch details for a Paddle subscription.

        Args:
            subscription_id: The Paddle subscription ID (``sub_...``).

        Returns:
            The full subscription object from Paddle.

        Raises:
            PaddleClientError: on non-2xx response or network failure.
        """
        url = f"{self.base_url}/subscriptions/{subscription_id}"

        logger.debug(
            "Fetching Paddle subscription",
            extra={"subscription_id": subscription_id},
        )

        return await self._get(url)

    async def get_transaction(self, transaction_id: str) -> dict[str, Any]:
        """Fetch details for a Paddle transaction.

        Args:
            transaction_id: The Paddle transaction ID (``txn_...``).

        Returns:
            The full transaction object from Paddle.

        Raises:
            PaddleClientError: on non-2xx response or network failure.
        """
        url = f"{self.base_url}/transactions/{transaction_id}"

        logger.debug(
            "Fetching Paddle transaction",
            extra={"transaction_id": transaction_id},
        )

        return await self._get(url)

    # ------------------------------------------------------------------
    # Prices / Catalog
    # ------------------------------------------------------------------

    async def get_price(self, price_id: str) -> dict[str, Any]:
        """Fetch a single price from the Paddle catalog.

        Returns the full price object including unit_price, billing_cycle, etc.
        """
        url = f"{self.base_url}/prices/{price_id}"
        return await self._get(url)

    # ------------------------------------------------------------------
    # Subscription plan changes
    # ------------------------------------------------------------------

    async def update_subscription(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_billing_mode: str = "prorated_immediately",
    ) -> dict[str, Any]:
        """Update a Paddle subscription's plan (price item).

        Used for upgrades and downgrades.  Paddle handles proration
        automatically based on *proration_billing_mode*.

        Args:
            subscription_id: The Paddle subscription ID (``sub_...``).
            new_price_id: The new Paddle price ID (``pri_...``).
            proration_billing_mode: One of ``"prorated_immediately"``,
                ``"prorated_next_billing_period"``, ``"full_immediately"``,
                ``"full_next_billing_period"``, ``"do_not_bill"``.

        Returns:
            The updated subscription object from Paddle.

        Raises:
            PaddleClientError: on non-2xx response or network failure.
        """
        url = f"{self.base_url}/subscriptions/{subscription_id}"
        payload: dict[str, Any] = {
            "items": [{"price_id": new_price_id, "quantity": 1}],
            "proration_billing_mode": proration_billing_mode,
        }

        logger.info(
            "Updating Paddle subscription plan",
            extra={
                "subscription_id": subscription_id,
                "new_price_id": new_price_id,
                "proration_billing_mode": proration_billing_mode,
            },
        )

        data = await self._patch(url, payload)

        logger.info(
            "Paddle subscription updated",
            extra={
                "subscription_id": subscription_id,
                "status": data.get("status"),
                "new_price_id": new_price_id,
            },
        )

        return data

    # ------------------------------------------------------------------
    # Refunds (Adjustments)
    # ------------------------------------------------------------------

    async def create_adjustment(
        self,
        transaction_id: str,
        reason: str = "refund",
        amount: Optional[int] = None,
    ) -> dict[str, Any]:
        """Create a Paddle adjustment (refund) for a transaction.

        Paddle uses the Adjustments API for refunds. If *amount* is
        ``None`` a full refund is issued.

        Args:
            transaction_id: The Paddle transaction ID (``txn_...``).
            reason: Human-readable reason for the adjustment.
            amount: Amount in smallest currency unit (cents). ``None``
                for full refund.

        Returns:
            The adjustment object from Paddle.

        Raises:
            PaddleClientError: on non-2xx response or network failure.
        """
        url = f"{self.base_url}/adjustments"
        payload: dict[str, Any] = {
            "action": "refund",
            "transaction_id": transaction_id,
            "reason": reason,
        }

        if amount is not None:
            payload["items"] = [{"item_id": transaction_id, "type": "partial", "amount": str(amount)}]

        logger.info(
            "Creating Paddle adjustment (refund)",
            extra={
                "transaction_id": transaction_id,
                "reason": reason,
                "amount": amount,
            },
        )

        data = await self._post(url, payload)

        logger.info(
            "Paddle adjustment created",
            extra={
                "adjustment_id": data.get("id"),
                "transaction_id": transaction_id,
                "status": data.get("status"),
            },
        )

        return data

    # ------------------------------------------------------------------
    # Internal HTTP helpers
    # ------------------------------------------------------------------

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a POST request and return the ``data`` envelope.

        Raises:
            PaddleClientError: on non-2xx or network errors.
        """
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.post(
                    url, json=payload, headers=self._build_headers(),
                )
                return self._handle_response(response)
        except httpx.HTTPError as exc:
            logger.error(
                "Paddle API POST failed",
                extra={"url": url, "error": str(exc)},
            )
            raise PaddleClientError(
                f"Paddle API request failed: {exc}",
            ) from exc

    async def _patch(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a PATCH request and return the ``data`` envelope.

        Raises:
            PaddleClientError: on non-2xx or network errors.
        """
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.patch(
                    url, json=payload, headers=self._build_headers(),
                )
                return self._handle_response(response)
        except httpx.HTTPError as exc:
            logger.error(
                "Paddle API PATCH failed",
                extra={"url": url, "error": str(exc)},
            )
            raise PaddleClientError(
                f"Paddle API request failed: {exc}",
            ) from exc

    async def _get(self, url: str) -> dict[str, Any]:
        """Execute a GET request and return the ``data`` envelope.

        Raises:
            PaddleClientError: on non-2xx or network errors.
        """
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.get(
                    url, headers=self._build_headers(),
                )
                return self._handle_response(response)
        except httpx.HTTPError as exc:
            logger.error(
                "Paddle API GET failed",
                extra={"url": url, "error": str(exc)},
            )
            raise PaddleClientError(
                f"Paddle API request failed: {exc}",
            ) from exc

    @staticmethod
    def _handle_response(response: httpx.Response) -> dict[str, Any]:
        """Parse a Paddle API response.

        Paddle wraps all payloads in ``{"data": {...}}``.  On error the
        response may contain ``{"error": {...}}``.

        Raises:
            PaddleClientError: when the status code is not 2xx.
        """
        try:
            body = response.json()
        except ValueError:
            body = {}

        if not response.is_success:
            error_detail = body.get("error", {})
            error_message = error_detail.get("detail", response.text[:300])
            logger.error(
                "Paddle API error response",
                extra={
                    "status_code": response.status_code,
                    "error_type": error_detail.get("type"),
                    "error_code": error_detail.get("code"),
                    "error_detail": error_message,
                },
            )
            raise PaddleClientError(
                message=f"Paddle API error ({response.status_code}): {error_message}",
                status_code=response.status_code,
                response_body=body,
            )

        return body.get("data", {})
