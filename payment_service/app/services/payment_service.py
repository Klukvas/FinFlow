from __future__ import annotations

import logging
import hashlib
import json
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.models import (
    Payment,
    PaymentEvent,
    PaymentStatus,
    PaymentProvider,
    PaymentPurpose,
    PaymentEventType,
)
from ..repositories.payment_repository import PaymentRepository
from ..repositories.payment_event_repository import PaymentEventRepository
from ..clients.wayforpay_client import WayForPayClient
from ..clients.subscription_client import SubscriptionClient
from ..schemas.payment import CreatePaymentRequest, WebhookWayForPayRequest
from ..config import settings
from ..utils.errors import ValidationError, ConflictError

logger = logging.getLogger("payment_service.payment_service")


class PaymentService:
    """Service for payment operations"""

    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.event_repo = PaymentEventRepository(db)
        self.wayforpay_client = WayForPayClient()
        self.subscription_client = SubscriptionClient()

    def create_payment(self, request: CreatePaymentRequest) -> Payment:
        """
        Create a new payment
        
        Args:
            request: Payment creation request
        
        Returns:
            Created payment
        
        Raises:
            ValidationError: If validation fails
        """
        # Validate request
        if request.purpose == PaymentPurpose.SUBSCRIPTION and not request.plan_code:
            raise ValidationError(
                "plan_code is required for SUBSCRIPTION purpose",
                error_code="@payment_service/MISSING_PLAN_CODE",
            )

        # Generate unique order reference
        order_reference = self._generate_order_reference()

        # Create payment record
        payment = Payment(
            id=uuid4(),
            provider=PaymentProvider.WAYFORPAY,
            order_reference=order_reference,
            user_id=request.user_id,
            workspace_id=request.workspace_id,
            purpose=request.purpose,
            plan_code=request.plan_code,
            amount=request.amount,
            currency=request.currency,
            status=PaymentStatus.CREATED,
            extra_data=request.metadata,
        )

        # Generate WayForPay payment form
        return_url = request.return_url or settings.wayforpay_return_url
        callback_url = settings.wayforpay_callback_url

        product_name = self._get_product_name(request)
        
        form_data = self.wayforpay_client.create_payment_form(
            order_reference=order_reference,
            amount=request.amount,
            currency=request.currency,
            product_name=product_name,
            product_count=1,
            product_price=request.amount,
            return_url=return_url,
            service_url=callback_url,
        )

        # Store form data and payment URL
        payment.provider_payload = form_data
        payment.provider_payment_url = "https://secure.wayforpay.com/pay"  # WayForPay checkout URL

        # Save payment
        payment = self.payment_repo.create(payment)

        # Create initial event
        event = PaymentEvent(
            id=uuid4(),
            payment_id=payment.id,
            event_type=PaymentEventType.CREATED,
            signature_valid=None,
            payload_raw={"request": request.model_dump(mode="json")},
            status_before=None,
            status_after=PaymentStatus.CREATED.value,
        )
        self.event_repo.create(event)

        logger.info(
            f"Payment created: {payment.id}",
            extra={
                "payment_id": str(payment.id),
                "order_reference": order_reference,
                "user_id": str(request.user_id),
                "amount": str(request.amount),
                "purpose": request.purpose.value,
            },
        )

        return payment

    async def process_wayforpay_callback(self, callback: WebhookWayForPayRequest) -> Payment:
        """
        Process WayForPay callback (webhook)
        
        Args:
            callback: Callback payload from WayForPay
        
        Returns:
            Updated payment
        
        Raises:
            ValidationError: If signature is invalid
            NotFoundError: If payment not found
        """
        order_reference = callback.orderReference

        # Verify signature
        signature_valid = self.wayforpay_client.verify_callback_signature(
            callback.model_dump(exclude_none=True)
        )

        if not signature_valid:
            logger.warning(
                f"Invalid signature for callback: {order_reference}",
                extra={
                    "order_reference": order_reference,
                    "merchant_account": callback.merchantAccount,
                },
            )
            raise ValidationError(
                "Invalid callback signature",
                error_code="@payment_service/INVALID_SIGNATURE",
                details={"order_reference": order_reference},
            )

        # Find payment
        payment = self.payment_repo.get_by_order_reference_or_raise(order_reference)

        # Check idempotency (prevent duplicate processing)
        provider_event_id = f"{order_reference}_{callback.transactionStatus}_{callback.createdDate}"
        payload_hash = self._compute_payload_hash(callback.model_dump(exclude_none=True))

        if self.event_repo.has_callback_been_processed(payment.id, provider_event_id, payload_hash):
            logger.info(
                f"Callback already processed for payment {payment.id}",
                extra={
                    "payment_id": str(payment.id),
                    "order_reference": order_reference,
                    "provider_event_id": provider_event_id,
                },
            )
            return payment

        # Determine new status based on transaction status
        old_status = payment.status
        new_status = self._map_wayforpay_status(callback.transactionStatus)

        # Create event
        event = PaymentEvent(
            id=uuid4(),
            payment_id=payment.id,
            event_type=PaymentEventType.CALLBACK,
            provider_event_id=provider_event_id,
            signature_valid=signature_valid,
            payload_raw=callback.model_dump(exclude_none=True),
            status_before=old_status.value,
            status_after=new_status.value,
        )
        self.event_repo.create(event)

        # Update payment status if changed
        if new_status != old_status:
            reason = callback.reason if callback.reason else None
            self.payment_repo.update_status(payment, new_status, reason=reason)

            # Notify downstream services
            if new_status == PaymentStatus.PAID:
                await self._notify_payment_success(payment)
            elif new_status in (PaymentStatus.FAILED, PaymentStatus.EXPIRED):
                await self._notify_payment_failure(payment, reason)

        logger.info(
            f"Processed callback for payment {payment.id}",
            extra={
                "payment_id": str(payment.id),
                "order_reference": order_reference,
                "transaction_status": callback.transactionStatus,
                "status_from": old_status.value,
                "status_to": new_status.value,
            },
        )

        return payment

    async def _notify_payment_success(self, payment: Payment):
        """Notify subscription_service about successful payment"""
        if payment.purpose != PaymentPurpose.SUBSCRIPTION or not payment.plan_code:
            logger.info(
                f"Payment {payment.id} is not a subscription payment, skipping notification",
                extra={"payment_id": str(payment.id), "purpose": payment.purpose.value},
            )
            return

        success = await self.subscription_client.notify_payment_success(
            payment_id=payment.id,
            user_id=payment.user_id,
            workspace_id=payment.workspace_id,
            plan_code=payment.plan_code,
            amount=payment.amount,
            currency=payment.currency,
        )

        if not success:
            logger.error(
                f"Failed to notify subscription_service about payment {payment.id}",
                extra={"payment_id": str(payment.id)},
            )
            # In production: store in outbox for retry

    async def _notify_payment_failure(self, payment: Payment, reason: Optional[str]):
        """Notify subscription_service about failed payment"""
        if payment.purpose != PaymentPurpose.SUBSCRIPTION:
            return

        await self.subscription_client.notify_payment_failure(
            payment_id=payment.id,
            user_id=payment.user_id,
            plan_code=payment.plan_code,
            reason=reason,
        )

    def _map_wayforpay_status(self, transaction_status: str) -> PaymentStatus:
        """Map WayForPay transaction status to internal payment status"""
        mapping = {
            "Approved": PaymentStatus.PAID,
            "Pending": PaymentStatus.PENDING,
            "Declined": PaymentStatus.FAILED,
            "Expired": PaymentStatus.EXPIRED,
            "Refunded": PaymentStatus.REFUNDED,
            "Voided": PaymentStatus.CANCELED,
        }
        return mapping.get(transaction_status, PaymentStatus.FAILED)

    def _generate_order_reference(self) -> str:
        """Generate unique order reference"""
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        return f"ORDER_{timestamp}_{uuid4().hex[:8]}"

    def _get_product_name(self, request: CreatePaymentRequest) -> str:
        """Get product name for payment"""
        if request.purpose == PaymentPurpose.SUBSCRIPTION:
            return f"Subscription: {request.plan_code}"
        return "One-time payment"

    def _compute_payload_hash(self, payload: dict) -> str:
        """Compute hash of payload for idempotency"""
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()
