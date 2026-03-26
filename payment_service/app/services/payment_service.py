from __future__ import annotations

import logging
import hashlib
import json
from decimal import Decimal
from typing import Optional, Any
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
    ProcessedWebhookEvent,
)
from ..repositories.payment_repository import PaymentRepository
from ..repositories.payment_event_repository import PaymentEventRepository
from ..clients.paddle_client import PaddleClient
from ..clients.subscription_client import SubscriptionClient
from ..schemas.payment import CreatePaymentRequest, ChangePlanRequest, PaddleWebhookEvent
from ..config import settings
from ..utils.errors import ValidationError, ConflictError
from ..utils.consent import validate_subscription_consent
from ..models.outbox import OutboxEvent
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger("payment_service.payment_service")


class PaymentService:
    """Service for payment operations via Paddle Billing."""

    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.event_repo = PaymentEventRepository(db)
        self.paddle_client = PaddleClient()
        self.subscription_client = SubscriptionClient()

    # ------------------------------------------------------------------
    # Payment creation
    # ------------------------------------------------------------------

    async def create_payment(self, request: CreatePaymentRequest) -> Payment:
        """Create a new payment via Paddle checkout.

        Validates the request, resolves the Paddle price from config,
        creates a Paddle checkout session, and persists the payment record.

        Args:
            request: Payment creation request.

        Returns:
            The newly created Payment.

        Raises:
            ValidationError: When request validation fails or price is not configured.
        """
        if request.purpose == PaymentPurpose.SUBSCRIPTION and not request.plan_code:
            raise ValidationError(
                "plan_code is required for SUBSCRIPTION purpose",
                error_code="@payment_service/MISSING_PLAN_CODE",
            )

        if request.purpose == PaymentPurpose.SUBSCRIPTION:
            validate_subscription_consent(request.metadata)

        # Resolve Paddle price_id from config
        price_mapping = settings.get_price_by_plan(request.plan_code)

        if not price_mapping:
            raise ValidationError(
                f"No Paddle price configured for plan '{request.plan_code}'",
                error_code="@payment_service/PRICE_NOT_CONFIGURED",
            )

        # Note: no server-side price validation — Paddle is the source of truth
        # for pricing via price_id. The amount from the frontend is for display only.

        # Prevent double-click double-charge: reject if active payment already exists
        existing_payment = self.payment_repo.get_active_payment_for_user_plan(
            user_id=str(request.user_id),
            plan_code=request.plan_code,
        )
        if existing_payment:
            raise ConflictError(
                f"Active payment already exists for plan '{request.plan_code}'",
                error_code="@payment_service/DUPLICATE_PAYMENT",
                details={"existing_payment_id": str(existing_payment.id)},
            )

        order_reference = self._generate_order_reference()
        payment_id = uuid4()

        # Build success URL with tracking params
        success_url = (
            f"{settings.paddle_success_url}?paymentId={payment_id}"
            f"&orderReference={order_reference}"
        )

        # Get user email from metadata
        user_email = ""
        if request.metadata:
            user_email = request.metadata.get("user_email", "")

        # Call Paddle API to create checkout session
        checkout_result = await self.paddle_client.create_checkout_session(
            customer_email=user_email,
            price_id=price_mapping.paddle_price_id,
            success_url=success_url,
            custom_data={
                "user_id": str(request.user_id),
                "workspace_id": str(request.workspace_id) if request.workspace_id else "",
                "order_reference": order_reference,
                "plan_code": request.plan_code or "",
            },
        )

        # Create payment record
        payment = Payment(
            id=payment_id,
            provider=PaymentProvider.PADDLE,
            order_reference=order_reference,
            user_id=request.user_id,
            workspace_id=request.workspace_id,
            purpose=request.purpose,
            plan_code=request.plan_code,
            amount=request.amount,
            currency=request.currency,
            status=PaymentStatus.CREATED,
            provider_payment_url=checkout_result.get("checkout_url", ""),
            paddle_transaction_id=checkout_result.get("transaction_id"),
            extra_data=request.metadata,
        )

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
                "checkout_url_present": bool(checkout_result.get("checkout_url")),
            },
        )

        return payment

    # ------------------------------------------------------------------
    # Recurring payment (scheduler renewals)
    # ------------------------------------------------------------------

    async def create_recurring_payment(
        self,
        user_id: str,
        subscription_id: Optional[int],
        plan_code: str,
        amount: Decimal,
        currency: str,
        recurring_token: str,
    ) -> Payment:
        """Create a recurring payment for subscription renewal.

        Called by the scheduler service to charge returning subscribers
        using a stored recurring token. Creates a Paddle transaction
        and persists the payment record.

        Args:
            user_id: User ID.
            subscription_id: Subscription ID from subscription_service.
            plan_code: Plan code being renewed.
            amount: Payment amount.
            currency: Currency code (e.g. ``"USD"``).
            recurring_token: Stored payment token for recurring billing.

        Returns:
            The newly created Payment.

        Raises:
            ValidationError: When required fields are missing.
        """
        if not plan_code:
            raise ValidationError(
                "plan_code is required for recurring payment",
                error_code="@payment_service/MISSING_PLAN_CODE",
            )

        if not recurring_token:
            raise ValidationError(
                "recurring_token is required for recurring payment",
                error_code="@payment_service/MISSING_RECURRING_TOKEN",
            )

        order_reference = self._generate_order_reference()
        payment_id = uuid4()

        payment = Payment(
            id=payment_id,
            provider=PaymentProvider.PADDLE,
            order_reference=order_reference,
            user_id=user_id,
            purpose=PaymentPurpose.SUBSCRIPTION,
            plan_code=plan_code,
            amount=amount,
            currency=currency,
            status=PaymentStatus.CREATED,
            extra_data={
                "source": "scheduler",
                "subscription_id": subscription_id,
                "recurring_token": recurring_token,
            },
        )

        payment = self.payment_repo.create(payment)

        # Create initial event
        event = PaymentEvent(
            id=uuid4(),
            payment_id=payment.id,
            event_type=PaymentEventType.CREATED,
            signature_valid=None,
            payload_raw={
                "source": "scheduler",
                "user_id": user_id,
                "subscription_id": subscription_id,
                "plan_code": plan_code,
                "amount": str(amount),
                "currency": currency,
            },
            status_before=None,
            status_after=PaymentStatus.CREATED.value,
        )
        self.event_repo.create(event)

        logger.info(
            f"Recurring payment created: {payment.id}",
            extra={
                "payment_id": str(payment.id),
                "order_reference": order_reference,
                "user_id": user_id,
                "subscription_id": subscription_id,
                "plan_code": plan_code,
                "amount": str(amount),
                "source": "scheduler",
            },
        )

        return payment

    # ------------------------------------------------------------------
    # Refunds
    # ------------------------------------------------------------------

    async def process_refund(
        self,
        payment: Payment,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> Payment:
        """Process a refund for a payment via the Paddle Adjustments API.

        Validates the payment is in PAID status, calls Paddle to create
        an adjustment, updates the payment status, and notifies
        subscription_service.

        Args:
            payment: The payment to refund.
            amount: Refund amount (``None`` for full refund).
            reason: Human-readable refund reason.

        Returns:
            The updated Payment with REFUNDED status.

        Raises:
            ValidationError: When payment is not in a refundable state
                or has no Paddle transaction ID.
        """
        if payment.status != PaymentStatus.PAID:
            raise ValidationError(
                f"Cannot refund payment in status '{payment.status.value}' — must be PAID",
                error_code="@payment_service/INVALID_REFUND_STATUS",
            )

        if not payment.paddle_transaction_id:
            raise ValidationError(
                "Cannot refund payment without a Paddle transaction ID",
                error_code="@payment_service/MISSING_TRANSACTION_ID",
            )

        # Convert amount to cents for Paddle API (if partial refund)
        paddle_amount: Optional[int] = None
        if amount is not None:
            paddle_amount = int(amount * 100)

        # Call Paddle Adjustments API
        adjustment = await self.paddle_client.create_adjustment(
            transaction_id=payment.paddle_transaction_id,
            reason=reason or "refund",
            amount=paddle_amount,
        )

        refunded_amount = amount if amount is not None else payment.amount

        # Update payment status
        old_status = payment.status
        self.payment_repo.update_status(payment, PaymentStatus.REFUNDED)

        # Create audit event
        pay_event = PaymentEvent(
            id=uuid4(),
            payment_id=payment.id,
            event_type=PaymentEventType.REFUND,
            signature_valid=None,
            payload_raw={
                "adjustment_id": adjustment.get("id"),
                "reason": reason,
                "refunded_amount": str(refunded_amount),
            },
            status_before=old_status.value,
            status_after=PaymentStatus.REFUNDED.value,
        )
        self.event_repo.create(pay_event)

        logger.info(
            f"Payment {payment.id} refunded",
            extra={
                "payment_id": str(payment.id),
                "adjustment_id": adjustment.get("id"),
                "refunded_amount": str(refunded_amount),
                "reason": reason,
            },
        )

        # Notify subscription_service
        await self._notify_payment_refunded(payment, reason)

        return payment

    # ------------------------------------------------------------------
    # Plan change (upgrade / downgrade)
    # ------------------------------------------------------------------

    async def change_subscription_plan(self, request: ChangePlanRequest) -> dict:
        """Change a Paddle subscription's plan via API update.

        Used for upgrades and downgrades. Paddle handles proration
        automatically. No new checkout session is needed.

        Args:
            request: Plan change request with user_id, new_plan_code,
                paddle_subscription_id, and metadata (consent).

        Returns:
            Dict with ``success``, ``old_plan_code``, ``new_plan_code``,
            ``paddle_subscription_id``.

        Raises:
            ValidationError: When consent is missing or price not configured.
        """
        # Validate consent
        validate_subscription_consent(request.metadata)

        # Resolve new Paddle price_id from config
        price_mapping = settings.get_price_by_plan(request.new_plan_code)

        if not price_mapping:
            raise ValidationError(
                f"No Paddle price configured for plan '{request.new_plan_code}'",
                error_code="@payment_service/PRICE_NOT_CONFIGURED",
            )

        # Resolve current plan_code from the existing price (reverse lookup)
        existing_sub = await self.paddle_client.get_subscription(
            request.paddle_subscription_id,
        )
        old_price_id = ""
        items = existing_sub.get("items") or []
        if items:
            old_price_id = items[0].get("price", {}).get("id", "")

        old_plan_code: Optional[str] = None
        if old_price_id:
            old_mapping = settings.get_price_by_paddle_id(old_price_id)
            if old_mapping:
                old_plan_code = old_mapping.plan_code

        logger.info(
            "Changing subscription plan",
            extra={
                "user_id": request.user_id,
                "paddle_subscription_id": request.paddle_subscription_id,
                "old_plan_code": old_plan_code,
                "new_plan_code": request.new_plan_code,
            },
        )

        # Call Paddle API to update the subscription
        updated_sub = await self.paddle_client.update_subscription(
            subscription_id=request.paddle_subscription_id,
            new_price_id=price_mapping.paddle_price_id,
        )

        logger.info(
            "Subscription plan changed successfully",
            extra={
                "paddle_subscription_id": request.paddle_subscription_id,
                "paddle_status": updated_sub.get("status"),
                "old_plan_code": old_plan_code,
                "new_plan_code": request.new_plan_code,
            },
        )

        # Extract currency from Paddle response (falls back to USD)
        paddle_currency = (updated_sub.get("currency_code") or "USD").upper()

        # Notify subscription_service about the plan change
        await self.subscription_client.notify_payment_success(
            payment_id=uuid4(),  # synthetic ID — no real payment for plan changes
            user_id=request.user_id,
            workspace_id=request.metadata.get("workspace_id") if request.metadata else None,
            plan_code=request.new_plan_code,
            amount=Decimal("0"),  # Paddle handles billing/proration
            currency=paddle_currency,
            paddle_subscription_id=request.paddle_subscription_id,
            paddle_price_id=price_mapping.paddle_price_id,
        )

        return {
            "success": True,
            "old_plan_code": old_plan_code,
            "new_plan_code": request.new_plan_code,
            "paddle_subscription_id": request.paddle_subscription_id,
        }

    # ------------------------------------------------------------------
    # Paddle webhook processing
    # ------------------------------------------------------------------

    async def process_paddle_webhook(self, event: PaddleWebhookEvent) -> Optional[Payment]:
        """Process a Paddle webhook event with idempotency.

        Checks whether the event has already been processed, routes to the
        appropriate handler, and records the event for deduplication.

        Args:
            event: The parsed Paddle webhook event.

        Returns:
            The affected Payment, or ``None`` when the event was already
            processed or does not map to a known handler.
        """
        # Idempotency: insert-first approach to avoid TOCTOU race condition.
        # If two concurrent requests process the same event_id, only one
        # succeeds — the other hits the UNIQUE constraint and returns early.
        processed = ProcessedWebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            payload_hash=self._compute_payload_hash(event.data),
        )
        try:
            self.db.add(processed)
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            logger.info(
                f"Webhook event already processed: {event.event_id}",
                extra={"event_id": event.event_id},
            )
            return None

        # Route by event type
        handler_map: dict[str, Any] = {
            "subscription.created": self._handle_subscription_created,
            "subscription.activated": self._handle_subscription_activated,
            "subscription.updated": self._handle_subscription_updated,
            "subscription.canceled": self._handle_subscription_canceled,
            "subscription.past_due": self._handle_subscription_past_due,
            "subscription.paused": self._handle_subscription_paused,
            "subscription.resumed": self._handle_subscription_resumed,
            "transaction.completed": self._handle_transaction_completed,
            "transaction.payment_failed": self._handle_transaction_payment_failed,
            "transaction.refunded": self._handle_transaction_refunded,
        }

        handler = handler_map.get(event.event_type)

        result: Optional[Payment] = None
        if handler:
            result = await handler(event)
        else:
            logger.warning(
                f"Unhandled Paddle event type: {event.event_type}",
                extra={"event_type": event.event_type},
            )

        self.db.commit()
        return result

    # ------------------------------------------------------------------
    # Transaction handlers
    # ------------------------------------------------------------------

    async def _handle_transaction_completed(self, event: PaddleWebhookEvent) -> Optional[Payment]:
        """Handle transaction.completed -- payment succeeded.

        Extracts custom_data (user_id, order_reference, plan_code),
        finds or creates the payment, updates status to PAID, and notifies
        subscription_service with Paddle IDs.
        """
        data = event.data
        custom_data = data.get("custom_data") or {}

        user_id = custom_data.get("user_id", "")
        order_reference = custom_data.get("order_reference", "")
        plan_code = custom_data.get("plan_code", "")
        workspace_id = custom_data.get("workspace_id", "")

        paddle_customer_id = data.get("customer_id", "")
        paddle_subscription_id = data.get("subscription_id", "")
        paddle_transaction_id = data.get("id", "")

        # Extract price_id from items
        paddle_price_id = ""
        items = data.get("items") or []
        if items and isinstance(items, list):
            first_item = items[0]
            paddle_price_id = first_item.get("price_id", "") or first_item.get("price", {}).get("id", "")

        # Find existing payment by order_reference or create one
        payment = self.payment_repo.get_by_order_reference(order_reference) if order_reference else None

        if not payment and user_id:
            # Payment might have been created outside normal flow; create a record
            webhook_amount_raw = data.get("details", {}).get("totals", {}).get("total", "0")
            try:
                webhook_amount = Decimal(str(webhook_amount_raw)) / 100
            except Exception:
                logger.error(
                    "Invalid amount in webhook data",
                    extra={"raw_amount": str(webhook_amount_raw), "event_id": event.event_id},
                )
                webhook_amount = Decimal("0")

            if webhook_amount <= 0 or webhook_amount > Decimal("100000"):
                logger.warning(
                    "Suspicious webhook amount",
                    extra={"amount": str(webhook_amount), "event_id": event.event_id},
                )

            payment = Payment(
                id=uuid4(),
                provider=PaymentProvider.PADDLE,
                order_reference=order_reference or self._generate_order_reference(),
                user_id=user_id,
                workspace_id=workspace_id or None,
                purpose=PaymentPurpose.SUBSCRIPTION if plan_code else PaymentPurpose.ONE_TIME,
                plan_code=plan_code or None,
                amount=webhook_amount,
                currency=data.get("currency_code", "USD"),
                status=PaymentStatus.CREATED,
                paddle_customer_id=paddle_customer_id,
                paddle_subscription_id=paddle_subscription_id or None,
                paddle_transaction_id=paddle_transaction_id,
            )
            payment = self.payment_repo.create(payment)

            logger.info(
                f"Created payment from webhook: {payment.id}",
                extra={
                    "payment_id": str(payment.id),
                    "order_reference": payment.order_reference,
                    "user_id": user_id,
                },
            )

        if not payment:
            logger.error(
                "Cannot resolve payment for transaction.completed",
                extra={
                    "event_id": event.event_id,
                    "order_reference": order_reference,
                    "transaction_id": paddle_transaction_id,
                },
            )
            return None

        # Update Paddle IDs on the payment
        payment.paddle_customer_id = paddle_customer_id or payment.paddle_customer_id
        payment.paddle_subscription_id = paddle_subscription_id or payment.paddle_subscription_id
        payment.paddle_transaction_id = paddle_transaction_id or payment.paddle_transaction_id

        old_status = payment.status

        # Update status to PAID
        self.payment_repo.update_status(payment, PaymentStatus.PAID)

        # Create event
        pay_event = PaymentEvent(
            id=uuid4(),
            payment_id=payment.id,
            event_type=PaymentEventType.CALLBACK,
            provider_event_id=event.event_id,
            signature_valid=True,
            payload_raw=data,
            status_before=old_status.value,
            status_after=PaymentStatus.PAID.value,
        )
        self.event_repo.create(pay_event)

        logger.info(
            f"Transaction completed for payment {payment.id}",
            extra={
                "payment_id": str(payment.id),
                "paddle_transaction_id": paddle_transaction_id,
                "paddle_subscription_id": paddle_subscription_id,
                "paddle_customer_id": paddle_customer_id,
                "old_status": old_status.value,
            },
        )

        # Notify subscription_service
        await self._notify_payment_success(
            payment,
            paddle_customer_id=paddle_customer_id,
            paddle_subscription_id=paddle_subscription_id,
            paddle_price_id=paddle_price_id,
        )

        return payment

    async def _handle_transaction_payment_failed(self, event: PaddleWebhookEvent) -> Optional[Payment]:
        """Handle transaction.payment_failed -- charge attempt failed."""
        data = event.data
        custom_data = data.get("custom_data") or {}

        order_reference = custom_data.get("order_reference", "")
        paddle_transaction_id = data.get("id", "")

        payment = self.payment_repo.get_by_order_reference(order_reference) if order_reference else None

        if not payment and paddle_transaction_id:
            # Try to find by paddle_transaction_id
            payment = (
                self.db.query(Payment)
                .filter(Payment.paddle_transaction_id == paddle_transaction_id)
                .first()
            )

        if not payment:
            logger.warning(
                "Payment not found for transaction.payment_failed",
                extra={
                    "event_id": event.event_id,
                    "order_reference": order_reference,
                    "transaction_id": paddle_transaction_id,
                },
            )
            return None

        old_status = payment.status
        failure_reason = data.get("payments", [{}])[0].get("error_code", "payment_failed") if data.get("payments") else "payment_failed"

        self.payment_repo.update_status(payment, PaymentStatus.FAILED, reason=failure_reason)

        pay_event = PaymentEvent(
            id=uuid4(),
            payment_id=payment.id,
            event_type=PaymentEventType.CALLBACK,
            provider_event_id=event.event_id,
            signature_valid=True,
            payload_raw=data,
            status_before=old_status.value,
            status_after=PaymentStatus.FAILED.value,
        )
        self.event_repo.create(pay_event)

        logger.info(
            f"Transaction payment failed for payment {payment.id}",
            extra={
                "payment_id": str(payment.id),
                "failure_reason": failure_reason,
            },
        )

        await self._notify_payment_failure(payment, failure_reason)

        return payment

    async def _handle_transaction_refunded(self, event: PaddleWebhookEvent) -> Optional[Payment]:
        """Handle transaction.refunded -- refund processed by Paddle."""
        data = event.data
        paddle_transaction_id = data.get("id", "")

        # Find payment by transaction ID
        payment = (
            self.db.query(Payment)
            .filter(Payment.paddle_transaction_id == paddle_transaction_id)
            .first()
        ) if paddle_transaction_id else None

        if not payment:
            custom_data = data.get("custom_data") or {}
            order_reference = custom_data.get("order_reference", "")
            payment = self.payment_repo.get_by_order_reference(order_reference) if order_reference else None

        if not payment:
            logger.warning(
                "Payment not found for transaction.refunded",
                extra={
                    "event_id": event.event_id,
                    "transaction_id": paddle_transaction_id,
                },
            )
            return None

        old_status = payment.status
        reason = data.get("reason", "refund")

        self.payment_repo.update_status(payment, PaymentStatus.REFUNDED, reason=reason)

        pay_event = PaymentEvent(
            id=uuid4(),
            payment_id=payment.id,
            event_type=PaymentEventType.REFUND,
            provider_event_id=event.event_id,
            signature_valid=True,
            payload_raw=data,
            status_before=old_status.value,
            status_after=PaymentStatus.REFUNDED.value,
        )
        self.event_repo.create(pay_event)

        logger.info(
            f"Transaction refunded for payment {payment.id}",
            extra={
                "payment_id": str(payment.id),
                "paddle_transaction_id": paddle_transaction_id,
                "reason": reason,
            },
        )

        await self._notify_payment_refunded(payment, reason)

        return payment

    # ------------------------------------------------------------------
    # Subscription handlers
    # ------------------------------------------------------------------

    async def _handle_subscription_created(self, event: PaddleWebhookEvent) -> Optional[Payment]:
        """Handle subscription.created -- log for audit, no status change."""
        data = event.data
        custom_data = data.get("custom_data") or {}
        user_id = custom_data.get("user_id", "")
        paddle_subscription_id = data.get("id", "")

        logger.info(
            "Paddle subscription created",
            extra={
                "event_id": event.event_id,
                "paddle_subscription_id": paddle_subscription_id,
                "user_id": user_id,
                "status": data.get("status"),
            },
        )

        # Store audit event on the payment if we can find it
        payment = self._find_payment_by_subscription_or_custom_data(data)
        if payment:
            pay_event = PaymentEvent(
                id=uuid4(),
                payment_id=payment.id,
                event_type=PaymentEventType.CALLBACK,
                provider_event_id=event.event_id,
                signature_valid=True,
                payload_raw=data,
                status_before=payment.status.value,
                status_after=payment.status.value,
            )
            self.event_repo.create(pay_event)

        return payment

    async def _handle_subscription_activated(self, event: PaddleWebhookEvent) -> Optional[Payment]:
        """Handle subscription.activated -- notify subscription_service to activate."""
        data = event.data
        custom_data = data.get("custom_data") or {}
        user_id = custom_data.get("user_id", "")
        paddle_subscription_id = data.get("id", "")
        paddle_customer_id = data.get("customer_id", "")

        # Extract price_id from items
        paddle_price_id = ""
        items = data.get("items") or []
        if items and isinstance(items, list):
            first_item = items[0]
            paddle_price_id = first_item.get("price_id", "") or first_item.get("price", {}).get("id", "")

        logger.info(
            "Paddle subscription activated",
            extra={
                "event_id": event.event_id,
                "paddle_subscription_id": paddle_subscription_id,
                "user_id": user_id,
            },
        )

        if user_id:
            await self.subscription_client.notify_paddle_subscription_event(
                user_id=user_id,
                paddle_subscription_id=paddle_subscription_id,
                event_type="activated",
            )

        # Store audit event
        payment = self._find_payment_by_subscription_or_custom_data(data)
        if payment:
            pay_event = PaymentEvent(
                id=uuid4(),
                payment_id=payment.id,
                event_type=PaymentEventType.CALLBACK,
                provider_event_id=event.event_id,
                signature_valid=True,
                payload_raw=data,
                status_before=payment.status.value,
                status_after=payment.status.value,
            )
            self.event_repo.create(pay_event)

        return payment

    async def _handle_subscription_updated(self, event: PaddleWebhookEvent) -> Optional[Payment]:
        """Handle subscription.updated -- detect plan changes and notify.

        When a subscription's price item changes (upgrade/downgrade),
        reverse-lookup the new plan_code from the price map config and notify
        subscription_service so it can update the user's plan.
        """
        data = event.data
        custom_data = data.get("custom_data") or {}
        user_id = custom_data.get("user_id", "")
        paddle_subscription_id = data.get("id", "")

        # Extract current price_id from items
        new_price_id = ""
        items = data.get("items") or []
        if items and isinstance(items, list):
            first_item = items[0]
            new_price_id = (
                first_item.get("price_id", "")
                or first_item.get("price", {}).get("id", "")
            )

        logger.info(
            "Paddle subscription updated",
            extra={
                "event_id": event.event_id,
                "paddle_subscription_id": paddle_subscription_id,
                "user_id": user_id,
                "status": data.get("status"),
                "new_price_id": new_price_id,
            },
        )

        # Reverse-lookup plan_code for the new price
        new_plan_code: Optional[str] = None
        if new_price_id:
            price_entry = settings.get_price_by_paddle_id(new_price_id)
            if price_entry:
                new_plan_code = price_entry.plan_code

        # If we resolved a plan_code, notify subscription_service
        if user_id and new_plan_code:
            logger.info(
                "Detected plan change via subscription.updated webhook",
                extra={
                    "user_id": user_id,
                    "new_plan_code": new_plan_code,
                    "new_price_id": new_price_id,
                    "paddle_subscription_id": paddle_subscription_id,
                },
            )

            webhook_currency = (data.get("currency_code") or "USD").upper()
            workspace_id = custom_data.get("workspace_id") or None

            await self.subscription_client.notify_payment_success(
                payment_id=uuid4(),  # synthetic ID — no real payment for webhook plan change
                user_id=user_id,
                workspace_id=workspace_id,
                plan_code=new_plan_code,
                amount=Decimal("0"),  # Paddle handles billing/proration
                currency=webhook_currency,
                paddle_subscription_id=paddle_subscription_id,
                paddle_price_id=new_price_id,
            )

        # Store audit event
        payment = self._find_payment_by_subscription_or_custom_data(data)
        if payment:
            pay_event = PaymentEvent(
                id=uuid4(),
                payment_id=payment.id,
                event_type=PaymentEventType.CALLBACK,
                provider_event_id=event.event_id,
                signature_valid=True,
                payload_raw=data,
                status_before=payment.status.value,
                status_after=payment.status.value,
            )
            self.event_repo.create(pay_event)

        return payment

    async def _handle_subscription_canceled(self, event: PaddleWebhookEvent) -> Optional[Payment]:
        """Handle subscription.canceled -- notify subscription_service."""
        data = event.data
        custom_data = data.get("custom_data") or {}
        user_id = custom_data.get("user_id", "")
        paddle_subscription_id = data.get("id", "")
        effective_from = data.get("scheduled_change", {}).get("effective_at", "") if data.get("scheduled_change") else ""

        logger.info(
            "Paddle subscription canceled",
            extra={
                "event_id": event.event_id,
                "paddle_subscription_id": paddle_subscription_id,
                "user_id": user_id,
                "effective_from": effective_from,
            },
        )

        if user_id:
            await self.subscription_client.notify_paddle_subscription_event(
                user_id=user_id,
                paddle_subscription_id=paddle_subscription_id,
                event_type="canceled",
                effective_from=effective_from or None,
            )

        payment = self._find_payment_by_subscription_or_custom_data(data)
        if payment:
            pay_event = PaymentEvent(
                id=uuid4(),
                payment_id=payment.id,
                event_type=PaymentEventType.CALLBACK,
                provider_event_id=event.event_id,
                signature_valid=True,
                payload_raw=data,
                status_before=payment.status.value,
                status_after=payment.status.value,
            )
            self.event_repo.create(pay_event)

        return payment

    async def _handle_subscription_past_due(self, event: PaddleWebhookEvent) -> Optional[Payment]:
        """Handle subscription.past_due -- notify subscription_service."""
        data = event.data
        custom_data = data.get("custom_data") or {}
        user_id = custom_data.get("user_id", "")
        paddle_subscription_id = data.get("id", "")

        logger.info(
            "Paddle subscription past due",
            extra={
                "event_id": event.event_id,
                "paddle_subscription_id": paddle_subscription_id,
                "user_id": user_id,
            },
        )

        if user_id:
            await self.subscription_client.notify_paddle_subscription_event(
                user_id=user_id,
                paddle_subscription_id=paddle_subscription_id,
                event_type="past_due",
            )

        payment = self._find_payment_by_subscription_or_custom_data(data)
        if payment:
            pay_event = PaymentEvent(
                id=uuid4(),
                payment_id=payment.id,
                event_type=PaymentEventType.CALLBACK,
                provider_event_id=event.event_id,
                signature_valid=True,
                payload_raw=data,
                status_before=payment.status.value,
                status_after=payment.status.value,
            )
            self.event_repo.create(pay_event)

        return payment

    async def _handle_subscription_paused(self, event: PaddleWebhookEvent) -> Optional[Payment]:
        """Handle subscription.paused -- notify subscription_service."""
        data = event.data
        custom_data = data.get("custom_data") or {}
        user_id = custom_data.get("user_id", "")
        paddle_subscription_id = data.get("id", "")
        effective_from = data.get("paused_at", "")

        logger.info(
            "Paddle subscription paused",
            extra={
                "event_id": event.event_id,
                "paddle_subscription_id": paddle_subscription_id,
                "user_id": user_id,
            },
        )

        if user_id:
            await self.subscription_client.notify_paddle_subscription_event(
                user_id=user_id,
                paddle_subscription_id=paddle_subscription_id,
                event_type="paused",
                effective_from=effective_from or None,
            )

        payment = self._find_payment_by_subscription_or_custom_data(data)
        if payment:
            pay_event = PaymentEvent(
                id=uuid4(),
                payment_id=payment.id,
                event_type=PaymentEventType.CALLBACK,
                provider_event_id=event.event_id,
                signature_valid=True,
                payload_raw=data,
                status_before=payment.status.value,
                status_after=payment.status.value,
            )
            self.event_repo.create(pay_event)

        return payment

    async def _handle_subscription_resumed(self, event: PaddleWebhookEvent) -> Optional[Payment]:
        """Handle subscription.resumed -- notify subscription_service."""
        data = event.data
        custom_data = data.get("custom_data") or {}
        user_id = custom_data.get("user_id", "")
        paddle_subscription_id = data.get("id", "")

        logger.info(
            "Paddle subscription resumed",
            extra={
                "event_id": event.event_id,
                "paddle_subscription_id": paddle_subscription_id,
                "user_id": user_id,
            },
        )

        if user_id:
            await self.subscription_client.notify_paddle_subscription_event(
                user_id=user_id,
                paddle_subscription_id=paddle_subscription_id,
                event_type="resumed",
            )

        payment = self._find_payment_by_subscription_or_custom_data(data)
        if payment:
            pay_event = PaymentEvent(
                id=uuid4(),
                payment_id=payment.id,
                event_type=PaymentEventType.CALLBACK,
                provider_event_id=event.event_id,
                signature_valid=True,
                payload_raw=data,
                status_before=payment.status.value,
                status_after=payment.status.value,
            )
            self.event_repo.create(pay_event)

        return payment

    # ------------------------------------------------------------------
    # Downstream notifications
    # ------------------------------------------------------------------

    async def _notify_payment_success(
        self,
        payment: Payment,
        paddle_customer_id: Optional[str] = None,
        paddle_subscription_id: Optional[str] = None,
        paddle_price_id: Optional[str] = None,
    ) -> None:
        """Queue notification to subscription_service about a successful payment via outbox."""
        if payment.purpose != PaymentPurpose.SUBSCRIPTION or not payment.plan_code:
            logger.info(
                f"Payment {payment.id} is not a subscription payment, skipping notification",
                extra={"payment_id": str(payment.id), "purpose": payment.purpose.value},
            )
            return

        payload = {
            "payment_id": str(payment.id),
            "user_id": payment.user_id,
            "workspace_id": payment.workspace_id,
            "plan_code": payment.plan_code,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "paddle_customer_id": paddle_customer_id,
            "paddle_subscription_id": paddle_subscription_id,
            "paddle_price_id": paddle_price_id,
        }

        outbox_event = OutboxEvent(
            aggregate_type="payment",
            aggregate_id=payment.id,
            event_type="payment_success",
            payload=payload,
            destination_url=f"{settings.subscription_service_url}/v1/internal/subscriptions/activate",
        )
        self.db.add(outbox_event)

        logger.info(
            f"Queued payment_success outbox event for payment {payment.id}",
            extra={"payment_id": str(payment.id), "outbox_event_id": str(outbox_event.id)},
        )

    async def _notify_payment_failure(self, payment: Payment, reason: Optional[str]) -> None:
        """Queue notification to subscription_service about a failed payment via outbox."""
        if payment.purpose != PaymentPurpose.SUBSCRIPTION:
            return

        payload = {
            "payment_id": str(payment.id),
            "user_id": payment.user_id,
            "plan_code": payment.plan_code,
            "reason": reason,
        }

        outbox_event = OutboxEvent(
            aggregate_type="payment",
            aggregate_id=payment.id,
            event_type="payment_failed",
            payload=payload,
            destination_url=f"{settings.subscription_service_url}/v1/internal/subscriptions/payment-failed",
        )
        self.db.add(outbox_event)

    async def _notify_payment_refunded(self, payment: Payment, reason: Optional[str]) -> None:
        """Queue notification to subscription_service about a refund via outbox."""
        if payment.purpose != PaymentPurpose.SUBSCRIPTION:
            logger.info(
                f"Payment {payment.id} is not a subscription payment, skipping refund notification",
                extra={"payment_id": str(payment.id), "purpose": payment.purpose.value},
            )
            return

        payload = {
            "payment_id": str(payment.id),
            "user_id": payment.user_id,
            "reason": reason,
        }

        outbox_event = OutboxEvent(
            aggregate_type="payment",
            aggregate_id=payment.id,
            event_type="payment_refunded",
            payload=payload,
            destination_url=f"{settings.subscription_service_url}/v1/internal/subscriptions/payment-refunded",
        )
        self.db.add(outbox_event)

        logger.info(
            f"Queued payment_refunded outbox event for payment {payment.id}",
            extra={"payment_id": str(payment.id)},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_payment_by_subscription_or_custom_data(self, data: dict[str, Any]) -> Optional[Payment]:
        """Try to find a payment matching the webhook data.

        Looks up by paddle_subscription_id first, then falls back to
        order_reference from custom_data.
        """
        paddle_subscription_id = data.get("id", "") or data.get("subscription_id", "")

        if paddle_subscription_id:
            payment = (
                self.db.query(Payment)
                .filter(Payment.paddle_subscription_id == paddle_subscription_id)
                .order_by(Payment.created_at.desc())
                .first()
            )
            if payment:
                return payment

        custom_data = data.get("custom_data") or {}
        order_reference = custom_data.get("order_reference", "")
        if order_reference:
            return self.payment_repo.get_by_order_reference(order_reference)

        return None

    @staticmethod
    def _generate_order_reference() -> str:
        """Generate a unique order reference."""
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        return f"ORDER_{timestamp}_{uuid4().hex[:16]}"

    @staticmethod
    def _get_product_name(request: CreatePaymentRequest) -> str:
        """Get product name for the payment."""
        if request.purpose == PaymentPurpose.SUBSCRIPTION:
            return f"Subscription: {request.plan_code}"
        return "One-time payment"

    @staticmethod
    def _compute_payload_hash(payload: dict) -> str:
        """Compute SHA-256 hash of payload for idempotency."""
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(payload_str.encode()).hexdigest()
