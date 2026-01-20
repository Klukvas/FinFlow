from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
from uuid import UUID

from ..config import settings
from ..database import SessionLocal
from ..clients import SubscriptionClient, PaymentClient
from ..repositories import JobRepository
from ..models.models import JobStatus
from ..utils.logging import get_logger
from ..utils import metrics

logger = get_logger("scheduler_service.subscription_renewal_job")


class SubscriptionRenewalJob:
    """
    Job that processes subscription renewals
    
    Responsibilities:
    - Identify subscriptions expiring soon
    - Attempt recurring payment
    - Extend subscription on success
    - Mark as past_due on failure
    - Track all attempts for audit
    """

    def __init__(self):
        self.subscription_client = SubscriptionClient()
        self.payment_client = PaymentClient()

    async def execute(self):
        """
        Main job execution entry point
        
        This method is called by the scheduler and handles the entire renewal process
        """
        job_name = "subscription_renewal"
        db = SessionLocal()
        job_repo = JobRepository(db)

        # Create job execution record
        job_execution = job_repo.create_job_execution(
            job_name=job_name,
            extra_data={"renewal_window_days": settings.renewal_window_days},
        )

        logger.info(
            f"Starting subscription renewal job",
            extra={"job_execution_id": str(job_execution.id)},
        )

        metrics.active_jobs_gauge.inc()
        start_time = datetime.utcnow()

        try:
            # Mark job as running
            job_repo.start_job(job_execution.id)

            # Get subscriptions expiring soon
            subscriptions = await self.subscription_client.get_expiring_subscriptions(
                days_ahead=settings.renewal_window_days
            )

            logger.info(
                f"Found {len(subscriptions)} subscriptions to renew",
                extra={
                    "job_execution_id": str(job_execution.id),
                    "count": len(subscriptions),
                },
            )

            # Process each subscription
            succeeded = 0
            failed = 0

            for subscription in subscriptions:
                try:
                    result = await self._process_subscription(
                        subscription, job_execution.id, job_repo
                    )
                    if result:
                        succeeded += 1
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(
                        f"Failed to process subscription {subscription.get('id')}: {e}",
                        extra={
                            "subscription_id": subscription.get("id"),
                            "error": str(e),
                        },
                    )
                    failed += 1

            # Mark job as completed
            job_repo.complete_job(
                job_execution_id=job_execution.id,
                status=JobStatus.SUCCESS,
                items_processed=len(subscriptions),
                items_succeeded=succeeded,
                items_failed=failed,
            )

            # Record metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics.record_job_execution(job_name, "success")
            metrics.record_job_duration(job_name, duration)

            logger.info(
                f"Completed subscription renewal job",
                extra={
                    "job_execution_id": str(job_execution.id),
                    "processed": len(subscriptions),
                    "succeeded": succeeded,
                    "failed": failed,
                    "duration_seconds": duration,
                },
            )

        except Exception as e:
            # Mark job as failed
            job_repo.complete_job(
                job_execution_id=job_execution.id,
                status=JobStatus.FAILED,
                error_message=str(e),
                error_details={"exception_type": type(e).__name__},
            )

            metrics.record_job_execution(job_name, "failed")

            logger.error(
                f"Subscription renewal job failed: {e}",
                extra={
                    "job_execution_id": str(job_execution.id),
                    "error": str(e),
                },
            )

            raise

        finally:
            metrics.active_jobs_gauge.dec()
            db.close()

    async def _process_subscription(
        self, subscription: Dict[str, Any], job_execution_id: UUID, job_repo: JobRepository
    ) -> bool:
        """
        Process a single subscription renewal
        
        Args:
            subscription: Subscription data
            job_execution_id: Job execution ID for tracking
            job_repo: Job repository
            
        Returns:
            True if renewal succeeded, False otherwise
        """
        subscription_id = subscription["id"]
        user_id = subscription["user_id"]
        plan_code = subscription["plan_code"]
        
        logger.info(
            f"Processing renewal for subscription {subscription_id}",
            extra={
                "subscription_id": subscription_id,
                "user_id": user_id,
                "plan_code": plan_code,
            },
        )

        # Check if subscription has recurring token
        recurring_token = subscription.get("recurring_token")
        if not recurring_token:
            logger.warning(
                f"Subscription {subscription_id} has no recurring token, skipping",
                extra={"subscription_id": subscription_id},
            )
            
            job_repo.create_renewal_attempt(
                job_execution_id=job_execution_id,
                subscription_id=subscription_id,
                user_id=user_id,
                amount="0",
                currency=subscription.get("currency", "UAH"),
                status="SKIPPED",
                failure_reason="no_recurring_token",
            )
            
            metrics.record_renewal_skipped("no_recurring_token")
            return False

        # Get plan details for amount
        amount = Decimal(subscription.get("plan_amount", "0"))
        currency = subscription.get("currency", "UAH")

        if amount <= 0:
            logger.warning(
                f"Subscription {subscription_id} has invalid amount, skipping",
                extra={"subscription_id": subscription_id, "amount": str(amount)},
            )
            
            job_repo.create_renewal_attempt(
                job_execution_id=job_execution_id,
                subscription_id=subscription_id,
                user_id=user_id,
                amount=str(amount),
                currency=currency,
                status="SKIPPED",
                failure_reason="invalid_amount",
            )
            
            metrics.record_renewal_skipped("invalid_amount")
            return False

        # Attempt recurring payment
        try:
            payment_result = await self.payment_client.create_recurring_payment(
                user_id=user_id,
                subscription_id=subscription_id,
                plan_code=plan_code,
                amount=amount,
                currency=currency,
                recurring_token=recurring_token,
            )

            payment_id = payment_result.get("payment_id")
            payment_status = payment_result.get("status")

            logger.info(
                f"Recurring payment created for subscription {subscription_id}",
                extra={
                    "subscription_id": subscription_id,
                    "payment_id": payment_id,
                    "status": payment_status,
                },
            )

            # Check payment status
            if payment_status == "PAID":
                # Success - extend subscription
                await self.subscription_client.extend_subscription(
                    subscription_id=subscription_id,
                    payment_id=payment_id,
                )

                job_repo.create_renewal_attempt(
                    job_execution_id=job_execution_id,
                    subscription_id=subscription_id,
                    user_id=user_id,
                    payment_id=UUID(payment_id) if payment_id else None,
                    amount=str(amount),
                    currency=currency,
                    status="SUCCESS",
                )

                metrics.record_renewal_attempt("success")
                return True

            else:
                # Payment failed or pending
                failure_reason = payment_result.get("failure_reason", payment_status)
                
                await self.subscription_client.mark_subscription_past_due(
                    subscription_id=subscription_id,
                    reason=failure_reason,
                )

                job_repo.create_renewal_attempt(
                    job_execution_id=job_execution_id,
                    subscription_id=subscription_id,
                    user_id=user_id,
                    payment_id=UUID(payment_id) if payment_id else None,
                    amount=str(amount),
                    currency=currency,
                    status="FAILED",
                    failure_reason=failure_reason,
                )

                metrics.record_renewal_attempt("failed")
                metrics.record_payment_failure(failure_reason)
                return False

        except Exception as e:
            # Payment creation failed
            logger.error(
                f"Failed to create recurring payment for subscription {subscription_id}: {e}",
                extra={
                    "subscription_id": subscription_id,
                    "error": str(e),
                },
            )

            await self.subscription_client.mark_subscription_past_due(
                subscription_id=subscription_id,
                reason=f"payment_error: {str(e)}",
            )

            job_repo.create_renewal_attempt(
                job_execution_id=job_execution_id,
                subscription_id=subscription_id,
                user_id=user_id,
                amount=str(amount),
                currency=currency,
                status="FAILED",
                failure_reason=str(e),
            )

            metrics.record_renewal_attempt("failed")
            metrics.record_payment_failure("payment_error")
            return False


# Global job instance
renewal_job = SubscriptionRenewalJob()
