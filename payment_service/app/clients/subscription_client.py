from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
import httpx

from ..config import settings

logger = logging.getLogger("payment_service.subscription_client")

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0  # 1s, 2s, 4s


class SubscriptionClient:
    """Client for communicating with subscription_service."""

    def __init__(self) -> None:
        self.base_url = settings.subscription_service_url.rstrip("/")
        self.internal_token = settings.internal_secret_token
        self._timeout = httpx.Timeout(connect=5.0, read=15.0, write=10.0, pool=5.0)

    # ------------------------------------------------------------------
    # Retry helper
    # ------------------------------------------------------------------

    async def _post_with_retry(
        self,
        url: str,
        payload: dict[str, Any],
        *,
        max_retries: int = MAX_RETRIES,
    ) -> tuple[bool, Optional[httpx.Response]]:
        """POST with exponential backoff retry.

        Retries on 5xx errors and connection/timeout failures.
        Returns immediately on 2xx success or 4xx client errors.

        Args:
            url: Target URL.
            payload: JSON body.
            max_retries: Maximum number of attempts.

        Returns:
            Tuple of (success: bool, response or None).
        """
        headers = self._build_headers()
        last_exc: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.is_success:
                        return True, response
                    # Don't retry on 4xx — it's a client error
                    if response.status_code < 500:
                        return False, response
                    last_exc = httpx.HTTPStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
                last_exc = exc
            except Exception as exc:
                last_exc = exc

            if attempt < max_retries:
                backoff = INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    f"Retry {attempt}/{max_retries} for {url} in {backoff}s",
                    extra={"url": url, "attempt": attempt, "backoff": backoff},
                )
                await asyncio.sleep(backoff)

        logger.error(
            f"All {max_retries} attempts failed for {url}",
            extra={"url": url, "last_error": str(last_exc)},
        )
        return False, None

    # ------------------------------------------------------------------
    # Payment lifecycle notifications
    # ------------------------------------------------------------------

    async def notify_payment_success(
        self,
        payment_id: UUID,
        user_id: str,
        workspace_id: Optional[str],
        plan_code: str,
        amount: Decimal,
        currency: str,
        recurring_token: Optional[str] = None,
        paddle_customer_id: Optional[str] = None,
        paddle_subscription_id: Optional[str] = None,
        paddle_price_id: Optional[str] = None,
    ) -> bool:
        """Notify subscription_service about a successful payment."""
        url = f"{self.base_url}/v1/internal/subscriptions/activate"

        payload: dict[str, Any] = {
            "payment_id": str(payment_id),
            "user_id": str(user_id),
            "workspace_id": str(workspace_id) if workspace_id else None,
            "plan_code": plan_code,
            "amount": str(amount),
            "currency": currency,
        }

        if recurring_token:
            payload["recurring_token"] = recurring_token
        if paddle_customer_id:
            payload["paddle_customer_id"] = paddle_customer_id
        if paddle_subscription_id:
            payload["paddle_subscription_id"] = paddle_subscription_id
        if paddle_price_id:
            payload["paddle_price_id"] = paddle_price_id

        success, _ = await self._post_with_retry(url, payload)

        if success:
            logger.info(
                f"Successfully notified subscription_service about payment {payment_id}",
                extra={
                    "payment_id": str(payment_id),
                    "user_id": str(user_id),
                    "plan_code": plan_code,
                    "has_paddle_ids": bool(paddle_subscription_id),
                },
            )
        else:
            logger.error(
                f"Failed to notify subscription_service about payment {payment_id} after retries",
                extra={"payment_id": str(payment_id)},
            )

        return success

    async def notify_payment_failure(
        self,
        payment_id: UUID,
        user_id: str,
        plan_code: Optional[str],
        reason: Optional[str],
    ) -> bool:
        """Notify subscription_service about a failed payment."""
        url = f"{self.base_url}/v1/internal/subscriptions/payment-failed"

        payload: dict[str, Any] = {
            "payment_id": str(payment_id),
            "user_id": str(user_id),
            "plan_code": plan_code,
            "reason": reason,
        }

        success, _ = await self._post_with_retry(url, payload)

        if success:
            logger.info(
                f"Notified subscription_service about payment failure {payment_id}",
                extra={"payment_id": str(payment_id)},
            )
        else:
            logger.warning(
                f"Failed to notify subscription_service about payment failure {payment_id}",
                extra={"payment_id": str(payment_id)},
            )

        return success

    async def notify_payment_refunded(
        self,
        payment_id: UUID,
        user_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Notify subscription_service about a refunded payment."""
        url = f"{self.base_url}/v1/internal/subscriptions/payment-refunded"

        payload: dict[str, Any] = {
            "payment_id": str(payment_id),
            "user_id": str(user_id),
            "reason": reason,
        }

        success, _ = await self._post_with_retry(url, payload)

        if success:
            logger.info(
                f"Notified subscription_service about payment refund {payment_id}",
                extra={"payment_id": str(payment_id), "user_id": str(user_id)},
            )
        else:
            logger.error(
                f"Failed to notify subscription_service about refund for payment {payment_id}",
                extra={"payment_id": str(payment_id)},
            )

        return success

    # ------------------------------------------------------------------
    # Paddle subscription lifecycle events
    # ------------------------------------------------------------------

    async def notify_paddle_subscription_event(
        self,
        user_id: str,
        paddle_subscription_id: str,
        event_type: str,
        effective_from: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """Notify subscription_service about a Paddle subscription lifecycle event."""
        url = f"{self.base_url}/v1/internal/subscriptions/paddle-event"

        payload: dict[str, Any] = {
            "user_id": user_id,
            "paddle_subscription_id": paddle_subscription_id,
            "event_type": event_type,
            "effective_from": effective_from,
            "reason": reason,
        }

        success, _ = await self._post_with_retry(url, payload)

        if success:
            logger.info(
                f"Notified subscription_service about Paddle event: {event_type}",
                extra={
                    "user_id": user_id,
                    "paddle_subscription_id": paddle_subscription_id,
                    "event_type": event_type,
                },
            )
        else:
            logger.error(
                f"Failed to notify subscription_service about Paddle event: {event_type}",
                extra={
                    "user_id": user_id,
                    "paddle_subscription_id": paddle_subscription_id,
                    "event_type": event_type,
                },
            )

        return success

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> dict[str, str]:
        """Return standard internal-auth headers."""
        return {
            "X-Internal-Token": self.internal_token,
            "Content-Type": "application/json",
        }
