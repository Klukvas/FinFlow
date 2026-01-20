from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from uuid import UUID

from ..models.models import JobExecution, RenewalAttempt, JobStatus


class JobRepository:
    """Repository for job execution tracking"""

    def __init__(self, db: Session):
        self.db = db

    def create_job_execution(self, job_name: str, extra_data: dict = None) -> JobExecution:
        """Create a new job execution record"""
        job_execution = JobExecution(
            job_name=job_name,
            status=JobStatus.PENDING,
            extra_data=extra_data or {},
        )
        self.db.add(job_execution)
        self.db.commit()
        self.db.refresh(job_execution)
        return job_execution

    def start_job(self, job_execution_id: UUID) -> JobExecution:
        """Mark job as started"""
        job = self.db.query(JobExecution).filter(JobExecution.id == job_execution_id).first()
        if job:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(job)
        return job

    def complete_job(
        self,
        job_execution_id: UUID,
        status: JobStatus,
        items_processed: int = 0,
        items_succeeded: int = 0,
        items_failed: int = 0,
        error_message: str = None,
        error_details: dict = None,
    ) -> JobExecution:
        """Mark job as completed"""
        job = self.db.query(JobExecution).filter(JobExecution.id == job_execution_id).first()
        if job:
            job.status = status
            job.completed_at = datetime.utcnow()
            job.items_processed = items_processed
            job.items_succeeded = items_succeeded
            job.items_failed = items_failed
            job.error_message = error_message
            job.error_details = error_details
            self.db.commit()
            self.db.refresh(job)
        return job

    def create_renewal_attempt(
        self,
        job_execution_id: UUID,
        subscription_id: int,
        user_id: str,
        amount: str,
        currency: str,
        status: str,
        payment_id: UUID = None,
        failure_reason: str = None,
        attempt_number: int = 1,
        extra_data: dict = None,
    ) -> RenewalAttempt:
        """Create a renewal attempt record"""
        attempt = RenewalAttempt(
            job_execution_id=job_execution_id,
            subscription_id=subscription_id,
            user_id=user_id,
            payment_id=payment_id,
            amount=amount,
            currency=currency,
            status=status,
            failure_reason=failure_reason,
            attempt_number=attempt_number,
            extra_data=extra_data or {},
        )
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt
