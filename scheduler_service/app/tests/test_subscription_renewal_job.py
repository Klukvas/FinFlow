"""Tests for SubscriptionRenewalJob — the core business logic.

All external dependencies (DB session, HTTP clients, distributed lock,
metrics) are mocked so tests run fast and in isolation.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from app.models.models import JobStatus
from app.jobs.subscription_renewal_job import (
    SubscriptionRenewalJob,
    RENEWAL_LOCK_NAME,
    RENEWAL_LOCK_TTL_SECONDS,
)
from app.tests.conftest import make_subscription


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_job(
    mock_subscription_client,
    mock_payment_client,
    mock_distributed_lock,
) -> SubscriptionRenewalJob:
    """Create a SubscriptionRenewalJob with injected mocks."""
    job = SubscriptionRenewalJob.__new__(SubscriptionRenewalJob)
    job.subscription_client = mock_subscription_client
    job.payment_client = mock_payment_client
    job.lock = mock_distributed_lock
    return job


def _mock_db_and_repo():
    """Return a (mock_db_session, mock_job_repo, mock_job_execution) triple."""
    mock_execution = MagicMock()
    mock_execution.id = uuid.uuid4()
    mock_execution.status = JobStatus.PENDING

    mock_repo = MagicMock()
    mock_repo.create_job_execution.return_value = mock_execution
    mock_repo.start_job.return_value = mock_execution
    mock_repo.complete_job.return_value = mock_execution
    mock_repo.create_renewal_attempt.return_value = MagicMock()
    mock_repo.count_recent_failures.return_value = 0

    mock_session = MagicMock()
    mock_session.close = MagicMock()

    return mock_session, mock_repo, mock_execution


# ---------------------------------------------------------------------------
# _process_subscription tests
# ---------------------------------------------------------------------------

class TestProcessSubscription:
    """Tests for _process_subscription which handles a single subscription."""

    @pytest.mark.asyncio
    async def test_successful_renewal(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """Happy path: payment succeeds, subscription is extended."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        payment_id = str(uuid.uuid4())
        mock_payment_client.create_recurring_payment.return_value = {
            "payment_id": payment_id,
            "status": "PAID",
        }

        sub = make_subscription()
        result = await job._process_subscription(sub, mock_exec.id, mock_repo)

        assert result is True
        mock_payment_client.create_recurring_payment.assert_called_once()
        mock_subscription_client.extend_subscription.assert_called_once_with(
            subscription_id=sub["id"],
            payment_id=payment_id,
        )
        mock_repo.create_renewal_attempt.assert_called_once()
        call_kwargs = mock_repo.create_renewal_attempt.call_args.kwargs
        assert call_kwargs["status"] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_skips_canceled_subscription(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """auto_renew=false means the user canceled; no payment should be attempted."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        sub = make_subscription(auto_renew=False)
        result = await job._process_subscription(sub, mock_exec.id, mock_repo)

        assert result is False
        mock_payment_client.create_recurring_payment.assert_not_called()
        call_kwargs = mock_repo.create_renewal_attempt.call_args.kwargs
        assert call_kwargs["status"] == "SKIPPED"
        assert "canceled" in call_kwargs["failure_reason"]

    @pytest.mark.asyncio
    async def test_skips_paddle_subscription(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """Paddle handles its own renewals; we should skip and return True (not a failure)."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        sub = make_subscription(payment_provider="PADDLE")
        result = await job._process_subscription(sub, mock_exec.id, mock_repo)

        assert result is True
        mock_payment_client.create_recurring_payment.assert_not_called()
        call_kwargs = mock_repo.create_renewal_attempt.call_args.kwargs
        assert call_kwargs["status"] == "SKIPPED"
        assert "paddle" in call_kwargs["failure_reason"]

    @pytest.mark.asyncio
    async def test_skips_no_recurring_token(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """Missing recurring token means we cannot charge; skip."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        sub = make_subscription(recurring_token=None)
        result = await job._process_subscription(sub, mock_exec.id, mock_repo)

        assert result is False
        mock_payment_client.create_recurring_payment.assert_not_called()
        call_kwargs = mock_repo.create_renewal_attempt.call_args.kwargs
        assert call_kwargs["status"] == "SKIPPED"
        assert "no_recurring_token" in call_kwargs["failure_reason"]

    @pytest.mark.asyncio
    async def test_skips_empty_recurring_token(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """Empty string recurring token is also treated as absent."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        sub = make_subscription(recurring_token="")
        result = await job._process_subscription(sub, mock_exec.id, mock_repo)

        assert result is False
        mock_payment_client.create_recurring_payment.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_zero_amount(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """Zero amount is invalid; skip."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        sub = make_subscription(plan_amount="0")
        result = await job._process_subscription(sub, mock_exec.id, mock_repo)

        assert result is False
        mock_payment_client.create_recurring_payment.assert_not_called()
        call_kwargs = mock_repo.create_renewal_attempt.call_args.kwargs
        assert call_kwargs["status"] == "SKIPPED"
        assert "invalid_amount" in call_kwargs["failure_reason"]

    @pytest.mark.asyncio
    async def test_skips_negative_amount(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """Negative amounts should not be charged."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        sub = make_subscription(plan_amount="-50.00")
        result = await job._process_subscription(sub, mock_exec.id, mock_repo)

        assert result is False
        mock_payment_client.create_recurring_payment.assert_not_called()

    @pytest.mark.asyncio
    async def test_payment_failure_records_attempt(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """When payment returns a non-PAID status, record as FAILED."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        mock_payment_client.create_recurring_payment.return_value = {
            "payment_id": str(uuid.uuid4()),
            "status": "DECLINED",
            "failure_reason": "insufficient_funds",
        }

        sub = make_subscription()
        result = await job._process_subscription(sub, mock_exec.id, mock_repo)

        assert result is False
        call_kwargs = mock_repo.create_renewal_attempt.call_args.kwargs
        assert call_kwargs["status"] == "FAILED"
        assert call_kwargs["failure_reason"] == "insufficient_funds"

    @pytest.mark.asyncio
    async def test_payment_exception_records_failed_attempt(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """When payment client raises, record a FAILED attempt and return False."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        mock_payment_client.create_recurring_payment.side_effect = Exception("timeout")

        sub = make_subscription()
        result = await job._process_subscription(sub, mock_exec.id, mock_repo)

        assert result is False
        call_kwargs = mock_repo.create_renewal_attempt.call_args.kwargs
        assert call_kwargs["status"] == "FAILED"
        assert "timeout" in call_kwargs["failure_reason"]

    @pytest.mark.asyncio
    async def test_payment_amount_and_currency_forwarded(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """Verify the correct amount and currency reach the payment client."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        mock_payment_client.create_recurring_payment.return_value = {
            "payment_id": str(uuid.uuid4()),
            "status": "PAID",
        }

        sub = make_subscription(plan_amount="499.99", currency="USD")
        await job._process_subscription(sub, mock_exec.id, mock_repo)

        call_kwargs = mock_payment_client.create_recurring_payment.call_args.kwargs
        assert call_kwargs["amount"] == Decimal("499.99")
        assert call_kwargs["currency"] == "USD"
        assert call_kwargs["plan_code"] == sub["plan_code"]

    @pytest.mark.asyncio
    async def test_subscription_not_extended_on_payment_failure(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """extend_subscription must NOT be called when payment fails."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        mock_payment_client.create_recurring_payment.return_value = {
            "payment_id": str(uuid.uuid4()),
            "status": "DECLINED",
        }

        sub = make_subscription()
        await job._process_subscription(sub, mock_exec.id, mock_repo)

        mock_subscription_client.extend_subscription.assert_not_called()

    @pytest.mark.asyncio
    async def test_default_currency_when_missing(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """When currency key is missing from subscription, defaults to UAH."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        _, mock_repo, mock_exec = _mock_db_and_repo()

        sub = make_subscription()
        del sub["currency"]  # remove currency key

        # Ensure amount > 0 and token present so we reach the payment call
        mock_payment_client.create_recurring_payment.return_value = {
            "payment_id": str(uuid.uuid4()),
            "status": "PAID",
        }

        await job._process_subscription(sub, mock_exec.id, mock_repo)

        call_kwargs = mock_payment_client.create_recurring_payment.call_args.kwargs
        assert call_kwargs["currency"] == "UAH"


# ---------------------------------------------------------------------------
# _handle_renewal_failure tests
# ---------------------------------------------------------------------------

class TestHandleRenewalFailure:
    """Tests for the retry-then-past-due escalation logic."""

    @pytest.mark.asyncio
    async def test_marks_past_due_when_max_retries_exceeded(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        mock_repo = MagicMock()
        mock_repo.count_recent_failures.return_value = 3  # == max_retry_attempts

        await job._handle_renewal_failure(
            subscription_id=42,
            reason="declined",
            job_repo=mock_repo,
        )

        mock_subscription_client.mark_subscription_past_due.assert_called_once_with(
            subscription_id=42,
            reason="declined",
        )

    @pytest.mark.asyncio
    async def test_does_not_mark_past_due_below_threshold(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        mock_repo = MagicMock()
        mock_repo.count_recent_failures.return_value = 1  # < max_retry_attempts (3)

        await job._handle_renewal_failure(
            subscription_id=42,
            reason="declined",
            job_repo=mock_repo,
        )

        mock_subscription_client.mark_subscription_past_due.assert_not_called()

    @pytest.mark.asyncio
    async def test_marks_past_due_when_failures_exceed_max(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """Even if count > max, still escalate."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        mock_repo = MagicMock()
        mock_repo.count_recent_failures.return_value = 10

        await job._handle_renewal_failure(
            subscription_id=42,
            reason="timeout",
            job_repo=mock_repo,
        )

        mock_subscription_client.mark_subscription_past_due.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_escalate_at_zero_failures(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        mock_repo = MagicMock()
        mock_repo.count_recent_failures.return_value = 0

        await job._handle_renewal_failure(
            subscription_id=42,
            reason="declined",
            job_repo=mock_repo,
        )

        mock_subscription_client.mark_subscription_past_due.assert_not_called()


# ---------------------------------------------------------------------------
# execute / _execute_inner tests
# ---------------------------------------------------------------------------

class TestExecuteInner:
    """Tests for the _execute_inner orchestration method."""

    @pytest.mark.asyncio
    async def test_full_happy_path(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """End-to-end: one subscription, payment succeeds, subscription extended."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)

        mock_session, mock_repo, mock_exec = _mock_db_and_repo()
        payment_id = str(uuid.uuid4())
        mock_payment_client.create_recurring_payment.return_value = {
            "payment_id": payment_id,
            "status": "PAID",
        }
        mock_subscription_client.get_expiring_subscriptions.return_value = [
            make_subscription()
        ]

        with patch("app.jobs.subscription_renewal_job.SessionLocal", return_value=mock_session), \
             patch("app.jobs.subscription_renewal_job.JobRepository", return_value=mock_repo):
            await job._execute_inner()

        mock_repo.create_job_execution.assert_called_once()
        mock_repo.start_job.assert_called_once_with(mock_exec.id)
        mock_repo.complete_job.assert_called_once()

        complete_kwargs = mock_repo.complete_job.call_args.kwargs
        assert complete_kwargs["status"] == JobStatus.SUCCESS
        assert complete_kwargs["items_processed"] == 1
        assert complete_kwargs["items_succeeded"] == 1
        assert complete_kwargs["items_failed"] == 0

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_marks_job_failed_on_fetch_error(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """If fetching expiring subscriptions fails, the job should be marked FAILED."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)

        mock_session, mock_repo, mock_exec = _mock_db_and_repo()
        mock_subscription_client.get_expiring_subscriptions.side_effect = Exception(
            "connection refused"
        )

        with patch("app.jobs.subscription_renewal_job.SessionLocal", return_value=mock_session), \
             patch("app.jobs.subscription_renewal_job.JobRepository", return_value=mock_repo):
            with pytest.raises(Exception, match="connection refused"):
                await job._execute_inner()

        complete_kwargs = mock_repo.complete_job.call_args.kwargs
        assert complete_kwargs["status"] == JobStatus.FAILED
        assert "connection refused" in complete_kwargs["error_message"]
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_processes_multiple_subscriptions(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """When multiple subscriptions are returned, each is processed."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)

        mock_session, mock_repo, mock_exec = _mock_db_and_repo()
        mock_payment_client.create_recurring_payment.return_value = {
            "payment_id": str(uuid.uuid4()),
            "status": "PAID",
        }

        subs = [make_subscription(subscription_id=i) for i in range(5)]
        mock_subscription_client.get_expiring_subscriptions.return_value = subs

        with patch("app.jobs.subscription_renewal_job.SessionLocal", return_value=mock_session), \
             patch("app.jobs.subscription_renewal_job.JobRepository", return_value=mock_repo):
            await job._execute_inner()

        complete_kwargs = mock_repo.complete_job.call_args.kwargs
        assert complete_kwargs["items_processed"] == 5
        assert complete_kwargs["items_succeeded"] == 5
        assert complete_kwargs["items_failed"] == 0

    @pytest.mark.asyncio
    async def test_partial_failure_counts_correctly(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """Mix of successes and failures results in correct counters."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)

        mock_session, mock_repo, mock_exec = _mock_db_and_repo()

        # Alternate success and failure
        def payment_side_effect(**kwargs):
            if kwargs["subscription_id"] % 2 == 0:
                return {"payment_id": str(uuid.uuid4()), "status": "PAID"}
            return {"payment_id": str(uuid.uuid4()), "status": "DECLINED"}

        mock_payment_client.create_recurring_payment.side_effect = payment_side_effect

        subs = [make_subscription(subscription_id=i) for i in range(4)]
        mock_subscription_client.get_expiring_subscriptions.return_value = subs

        with patch("app.jobs.subscription_renewal_job.SessionLocal", return_value=mock_session), \
             patch("app.jobs.subscription_renewal_job.JobRepository", return_value=mock_repo):
            await job._execute_inner()

        complete_kwargs = mock_repo.complete_job.call_args.kwargs
        assert complete_kwargs["items_processed"] == 4
        assert complete_kwargs["items_succeeded"] == 2  # ids 0, 2
        assert complete_kwargs["items_failed"] == 2     # ids 1, 3

    @pytest.mark.asyncio
    async def test_no_subscriptions_results_in_zero_counts(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """Empty list of subscriptions = zero processed."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)

        mock_session, mock_repo, mock_exec = _mock_db_and_repo()
        mock_subscription_client.get_expiring_subscriptions.return_value = []

        with patch("app.jobs.subscription_renewal_job.SessionLocal", return_value=mock_session), \
             patch("app.jobs.subscription_renewal_job.JobRepository", return_value=mock_repo):
            await job._execute_inner()

        complete_kwargs = mock_repo.complete_job.call_args.kwargs
        assert complete_kwargs["items_processed"] == 0
        assert complete_kwargs["status"] == JobStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_exception_in_process_subscription_counted_as_failure(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        """If _process_subscription raises unexpectedly, it counts as a failure."""
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)

        mock_session, mock_repo, mock_exec = _mock_db_and_repo()
        mock_subscription_client.get_expiring_subscriptions.return_value = [
            make_subscription()
        ]
        mock_payment_client.create_recurring_payment.side_effect = RuntimeError("boom")

        with patch("app.jobs.subscription_renewal_job.SessionLocal", return_value=mock_session), \
             patch("app.jobs.subscription_renewal_job.JobRepository", return_value=mock_repo):
            await job._execute_inner()

        # The individual exception is caught, job still completes as SUCCESS (at job level)
        complete_kwargs = mock_repo.complete_job.call_args.kwargs
        assert complete_kwargs["status"] == JobStatus.SUCCESS
        assert complete_kwargs["items_failed"] == 1

    @pytest.mark.asyncio
    async def test_db_session_closed_on_success(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        mock_session, mock_repo, mock_exec = _mock_db_and_repo()
        mock_subscription_client.get_expiring_subscriptions.return_value = []

        with patch("app.jobs.subscription_renewal_job.SessionLocal", return_value=mock_session), \
             patch("app.jobs.subscription_renewal_job.JobRepository", return_value=mock_repo):
            await job._execute_inner()

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_session_closed_on_failure(
        self, mock_subscription_client, mock_payment_client, mock_distributed_lock
    ):
        job = _build_job(mock_subscription_client, mock_payment_client, mock_distributed_lock)
        mock_session, mock_repo, mock_exec = _mock_db_and_repo()
        mock_subscription_client.get_expiring_subscriptions.side_effect = Exception("fail")

        with patch("app.jobs.subscription_renewal_job.SessionLocal", return_value=mock_session), \
             patch("app.jobs.subscription_renewal_job.JobRepository", return_value=mock_repo):
            with pytest.raises(Exception):
                await job._execute_inner()

        mock_session.close.assert_called_once()


# ---------------------------------------------------------------------------
# execute (with distributed lock) tests
# ---------------------------------------------------------------------------

class TestExecuteWithLock:
    """Tests for the execute() entry point that acquires the distributed lock."""

    @pytest.mark.asyncio
    async def test_skips_when_lock_not_acquired(
        self, mock_subscription_client, mock_payment_client
    ):
        """If another instance holds the lock, execution should be skipped entirely."""
        mock_lock = AsyncMock()

        # Simulate lock NOT acquired
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _fake_hold(name, ttl):
            yield False

        mock_lock.hold = _fake_hold

        job = _build_job(mock_subscription_client, mock_payment_client, mock_lock)

        with patch.object(job, "_execute_inner", new_callable=AsyncMock) as mock_inner:
            await job.execute()
            mock_inner.assert_not_called()

    @pytest.mark.asyncio
    async def test_runs_when_lock_acquired(
        self, mock_subscription_client, mock_payment_client
    ):
        """When lock is acquired, _execute_inner should be called."""
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _fake_hold(name, ttl):
            yield True

        mock_lock = AsyncMock()
        mock_lock.hold = _fake_hold

        job = _build_job(mock_subscription_client, mock_payment_client, mock_lock)

        with patch.object(job, "_execute_inner", new_callable=AsyncMock) as mock_inner:
            await job.execute()
            mock_inner.assert_called_once()
