from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID
import httpx

from ..config import settings

logger = logging.getLogger("payment_service.subscription_client")


class SubscriptionClient:
    """Client for communicating with subscription_service"""

    def __init__(self):
        self.base_url = settings.subscription_service_url.rstrip("/")
        self.internal_token = settings.internal_secret_token

    async def notify_payment_success(
        self,
        payment_id: UUID,
        user_id: str,
        workspace_id: Optional[str],
        plan_code: str,
        amount: Decimal,
        currency: str,
    ) -> bool:
        """
        Notify subscription_service about successful payment
        
        Args:
            payment_id: Payment ID
            user_id: User ID who made the payment
            workspace_id: Workspace ID (if applicable)
            plan_code: Plan code to activate
            amount: Payment amount
            currency: Payment currency
        
        Returns:
            True if notification was successful
        """
        url = f"{self.base_url}/v1/internal/subscriptions/activate"
        
        payload = {
            "payment_id": str(payment_id),
            "user_id": str(user_id),
            "workspace_id": str(workspace_id) if workspace_id else None,
            "plan_code": plan_code,
            "amount": str(amount),
            "currency": currency,
        }

        headers = {
            "X-Internal-Token": self.internal_token,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                logger.info(
                    f"Successfully notified subscription_service about payment {payment_id}",
                    extra={
                        "payment_id": str(payment_id),
                        "user_id": str(user_id),
                        "plan_code": plan_code,
                    },
                )
                return True

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to notify subscription_service (HTTP {e.response.status_code}): {e}",
                extra={
                    "payment_id": str(payment_id),
                    "status_code": e.response.status_code,
                    "error": str(e),
                },
            )
            return False

        except Exception as e:
            logger.error(
                f"Failed to notify subscription_service: {e}",
                extra={
                    "payment_id": str(payment_id),
                    "error": str(e),
                },
            )
            return False

    async def notify_payment_failure(
        self,
        payment_id: UUID,
        user_id: str,
        plan_code: Optional[str],
        reason: Optional[str],
    ) -> bool:
        """
        Notify subscription_service about failed payment
        
        Args:
            payment_id: Payment ID
            user_id: User ID
            plan_code: Plan code (if applicable)
            reason: Failure reason
        
        Returns:
            True if notification was successful
        """
        url = f"{self.base_url}/v1/internal/subscriptions/payment-failed"
        
        payload = {
            "payment_id": str(payment_id),
            "user_id": str(user_id),
            "plan_code": plan_code,
            "reason": reason,
        }

        headers = {
            "X-Internal-Token": self.internal_token,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                # Don't raise on 4xx/5xx - this is optional notification
                
                if response.is_success:
                    logger.info(
                        f"Notified subscription_service about payment failure {payment_id}",
                        extra={"payment_id": str(payment_id)},
                    )
                    return True
                else:
                    logger.warning(
                        f"Failed to notify subscription_service about payment failure",
                        extra={
                            "payment_id": str(payment_id),
                            "status_code": response.status_code,
                        },
                    )
                    return False

        except Exception as e:
            logger.warning(
                f"Exception notifying subscription_service about payment failure: {e}",
                extra={"payment_id": str(payment_id), "error": str(e)},
            )
            return False

    async def notify_payment_refunded(
        self,
        payment_id: UUID,
        user_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Notify subscription_service about refunded/chargebacked payment.
        
        This will cancel the user's subscription.
        
        Args:
            payment_id: Payment ID
            user_id: User ID
            reason: Refund reason
        
        Returns:
            True if notification was successful
        """
        url = f"{self.base_url}/v1/internal/subscriptions/payment-refunded"
        
        payload = {
            "payment_id": str(payment_id),
            "user_id": str(user_id),
            "reason": reason,
        }

        headers = {
            "X-Internal-Token": self.internal_token,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                logger.info(
                    f"Notified subscription_service about payment refund {payment_id}",
                    extra={
                        "payment_id": str(payment_id),
                        "user_id": str(user_id),
                    },
                )
                return True

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to notify subscription_service about refund (HTTP {e.response.status_code}): {e}",
                extra={
                    "payment_id": str(payment_id),
                    "status_code": e.response.status_code,
                    "error": str(e),
                },
            )
            return False

        except Exception as e:
            logger.error(
                f"Failed to notify subscription_service about refund: {e}",
                extra={
                    "payment_id": str(payment_id),
                    "error": str(e),
                },
            )
            return False
