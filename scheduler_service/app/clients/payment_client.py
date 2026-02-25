from __future__ import annotations

import hashlib
import httpx
from datetime import date
from typing import Dict, Any, Optional
from decimal import Decimal

from ..config import settings
from ..utils.logging import get_logger

logger = get_logger("scheduler_service.payment_client")


class PaymentClient:
    """Client for payment_service"""

    def __init__(self):
        self.base_url = settings.payment_service_url
        self.internal_token = settings.internal_secret_token

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for internal API calls"""
        return {
            "X-Internal-Token": self.internal_token,
            "Content-Type": "application/json",
        }

    async def create_recurring_payment(
        self,
        user_id: str,
        subscription_id: int,
        plan_code: str,
        amount: Decimal,
        currency: str,
        recurring_token: str,
    ) -> Dict[str, Any]:
        """
        Create recurring payment using stored payment token
        
        Args:
            user_id: User ID
            subscription_id: Subscription ID
            plan_code: Plan code
            amount: Payment amount
            currency: Currency code
            recurring_token: Stored recurring payment token
            
        Returns:
            Payment creation response
        """
        url = f"{self.base_url}/v1/internal/payments:recurring"

        # Deterministic idempotency key prevents duplicate charges on retry
        idempotency_key = hashlib.sha256(
            f"renewal_{subscription_id}_{date.today().isoformat()}".encode()
        ).hexdigest()

        payload = {
            "user_id": user_id,
            "subscription_id": subscription_id,
            "plan_code": plan_code,
            "amount": str(amount),
            "currency": currency,
            "recurring_token": recurring_token,
        }

        headers = {**self._get_headers(), "Idempotency-Key": idempotency_key}

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url, json=payload, headers=headers
                )
                response.raise_for_status()
                data = response.json()

                logger.info(
                    f"Created recurring payment for subscription {subscription_id}",
                    extra={
                        "subscription_id": subscription_id,
                        "user_id": user_id,
                        "payment_id": data.get("payment_id"),
                        "amount": str(amount),
                        "currency": currency,
                    },
                )

                return data
        except Exception as e:
            logger.error(
                f"Failed to create recurring payment for subscription {subscription_id}: {e}",
                extra={
                    "subscription_id": subscription_id,
                    "user_id": user_id,
                    "error": str(e),
                },
            )
            raise

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get payment status
        
        Args:
            payment_id: Payment ID
            
        Returns:
            Payment details
        """
        url = f"{self.base_url}/v1/internal/payments/{payment_id}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()

                logger.info(
                    f"Retrieved payment status for {payment_id}",
                    extra={
                        "payment_id": payment_id,
                        "status": data.get("status"),
                    },
                )

                return data
        except Exception as e:
            logger.error(
                f"Failed to get payment status for {payment_id}: {e}",
                extra={"payment_id": payment_id, "error": str(e)},
            )
            raise
