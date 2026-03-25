"""Tests for JobRepository — CRUD for job executions and renewal attempts.

Uses an in-memory SQLite database (see conftest.py).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest

from app.models.models import JobExecution, RenewalAttempt, JobStatus


class TestCreateJobExecution:
    def test_creates_pending_record(self, job_repo, db_session):
        job = job_repo.create_job_execution("subscription_renewal")

        assert job.id is not None
        assert job.job_name == "subscription_renewal"
        assert job.status == JobStatus.PENDING
        assert job.items_processed == 0
        assert job.error_message is None

    def test_stores_extra_data(self, job_repo, db_session):
        extra = {"renewal_window_days": 1}
        job = job_repo.create_job_execution("subscription_renewal", extra_data=extra)

        assert job.extra_data == extra

    def test_default_extra_data_is_empty_dict(self, job_repo, db_session):
        job = job_repo.create_job_execution("test_job")

        assert job.extra_data == {}

    def test_multiple_executions_have_unique_ids(self, job_repo, db_session):
        job1 = job_repo.create_job_execution("job_a")
        job2 = job_repo.create_job_execution("job_b")

        assert job1.id != job2.id


class TestStartJob:
    def test_transitions_to_running(self, job_repo, db_session):
        job = job_repo.create_job_execution("test_job")

        started = job_repo.start_job(job.id)

        assert started.status == JobStatus.RUNNING
        assert started.started_at is not None

    def test_returns_none_for_nonexistent_id(self, job_repo, db_session):
        result = job_repo.start_job(uuid.uuid4())

        assert result is None


class TestCompleteJob:
    def test_marks_success_with_counts(self, job_repo, db_session):
        job = job_repo.create_job_execution("test_job")
        job_repo.start_job(job.id)

        completed = job_repo.complete_job(
            job_execution_id=job.id,
            status=JobStatus.SUCCESS,
            items_processed=10,
            items_succeeded=8,
            items_failed=2,
        )

        assert completed.status == JobStatus.SUCCESS
        assert completed.completed_at is not None
        assert completed.items_processed == 10
        assert completed.items_succeeded == 8
        assert completed.items_failed == 2
        assert completed.error_message is None

    def test_marks_failed_with_error(self, job_repo, db_session):
        job = job_repo.create_job_execution("test_job")
        job_repo.start_job(job.id)

        completed = job_repo.complete_job(
            job_execution_id=job.id,
            status=JobStatus.FAILED,
            error_message="Connection timed out",
            error_details={"exception_type": "TimeoutError"},
        )

        assert completed.status == JobStatus.FAILED
        assert completed.error_message == "Connection timed out"
        assert completed.error_details == {"exception_type": "TimeoutError"}

    def test_returns_none_for_nonexistent_id(self, job_repo, db_session):
        result = job_repo.complete_job(
            job_execution_id=uuid.uuid4(),
            status=JobStatus.FAILED,
        )

        assert result is None

    def test_completed_at_is_set(self, job_repo, db_session):
        job = job_repo.create_job_execution("test_job")
        before = datetime.utcnow()

        completed = job_repo.complete_job(
            job_execution_id=job.id,
            status=JobStatus.SUCCESS,
        )

        assert completed.completed_at >= before


class TestCreateRenewalAttempt:
    def test_creates_success_attempt(self, job_repo, db_session):
        job = job_repo.create_job_execution("subscription_renewal")
        payment_id = uuid.uuid4()

        attempt = job_repo.create_renewal_attempt(
            job_execution_id=job.id,
            subscription_id=42,
            user_id="user-abc",
            amount="199.00",
            currency="UAH",
            status="SUCCESS",
            payment_id=payment_id,
        )

        assert attempt.id is not None
        assert attempt.subscription_id == 42
        assert attempt.user_id == "user-abc"
        assert attempt.amount == "199.00"
        assert attempt.currency == "UAH"
        assert attempt.status == "SUCCESS"
        assert attempt.payment_id == payment_id
        assert attempt.failure_reason is None
        assert attempt.attempt_number == 1

    def test_creates_failed_attempt_with_reason(self, job_repo, db_session):
        job = job_repo.create_job_execution("subscription_renewal")

        attempt = job_repo.create_renewal_attempt(
            job_execution_id=job.id,
            subscription_id=42,
            user_id="user-abc",
            amount="199.00",
            currency="UAH",
            status="FAILED",
            failure_reason="insufficient_funds",
            attempt_number=2,
        )

        assert attempt.status == "FAILED"
        assert attempt.failure_reason == "insufficient_funds"
        assert attempt.attempt_number == 2

    def test_creates_skipped_attempt(self, job_repo, db_session):
        job = job_repo.create_job_execution("subscription_renewal")

        attempt = job_repo.create_renewal_attempt(
            job_execution_id=job.id,
            subscription_id=99,
            user_id="user-xyz",
            amount="0",
            currency="UAH",
            status="SKIPPED",
            failure_reason="no_recurring_token",
        )

        assert attempt.status == "SKIPPED"
        assert attempt.failure_reason == "no_recurring_token"

    def test_extra_data_defaults_to_empty(self, job_repo, db_session):
        job = job_repo.create_job_execution("subscription_renewal")

        attempt = job_repo.create_renewal_attempt(
            job_execution_id=job.id,
            subscription_id=1,
            user_id="u",
            amount="10",
            currency="USD",
            status="SUCCESS",
        )

        assert attempt.extra_data == {}


class TestCountRecentFailures:
    def test_zero_when_no_failures(self, job_repo, db_session):
        count = job_repo.count_recent_failures(subscription_id=999)

        assert count == 0

    def test_counts_failed_within_window(self, job_repo, db_session):
        job = job_repo.create_job_execution("subscription_renewal")

        for _ in range(3):
            job_repo.create_renewal_attempt(
                job_execution_id=job.id,
                subscription_id=42,
                user_id="u",
                amount="100",
                currency="UAH",
                status="FAILED",
                failure_reason="declined",
            )

        count = job_repo.count_recent_failures(42, window_days=7)

        assert count == 3

    def test_ignores_successful_attempts(self, job_repo, db_session):
        job = job_repo.create_job_execution("subscription_renewal")

        job_repo.create_renewal_attempt(
            job_execution_id=job.id,
            subscription_id=42,
            user_id="u",
            amount="100",
            currency="UAH",
            status="SUCCESS",
        )
        job_repo.create_renewal_attempt(
            job_execution_id=job.id,
            subscription_id=42,
            user_id="u",
            amount="100",
            currency="UAH",
            status="FAILED",
            failure_reason="declined",
        )

        count = job_repo.count_recent_failures(42)

        assert count == 1

    def test_ignores_other_subscriptions(self, job_repo, db_session):
        job = job_repo.create_job_execution("subscription_renewal")

        job_repo.create_renewal_attempt(
            job_execution_id=job.id,
            subscription_id=100,
            user_id="u",
            amount="10",
            currency="UAH",
            status="FAILED",
            failure_reason="declined",
        )

        count = job_repo.count_recent_failures(subscription_id=200)

        assert count == 0

    def test_respects_custom_window(self, job_repo, db_session):
        """Failures created NOW should be within any window >= 0 days."""
        job = job_repo.create_job_execution("subscription_renewal")

        job_repo.create_renewal_attempt(
            job_execution_id=job.id,
            subscription_id=42,
            user_id="u",
            amount="100",
            currency="UAH",
            status="FAILED",
            failure_reason="declined",
        )

        # A 1-day window should include a record created just now.
        count = job_repo.count_recent_failures(42, window_days=1)
        assert count == 1
