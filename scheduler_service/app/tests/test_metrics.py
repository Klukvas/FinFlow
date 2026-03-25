"""Tests for the no-op metrics stubs.

Ensures all metrics functions exist and can be called without raising,
since they are used throughout the job execution code.
"""
from __future__ import annotations

from app.utils.metrics import (
    active_jobs_gauge,
    record_job_execution,
    record_job_duration,
    record_items_processed,
    record_renewal_attempt,
    record_payment_failure,
    record_renewal_skipped,
)


class TestActiveJobsGauge:
    def test_inc_does_not_raise(self):
        active_jobs_gauge.inc()

    def test_dec_does_not_raise(self):
        active_jobs_gauge.dec()

    def test_inc_dec_round_trip(self):
        """Calling inc then dec should not raise."""
        active_jobs_gauge.inc()
        active_jobs_gauge.dec()


class TestRecordFunctions:
    def test_record_job_execution_does_not_raise(self):
        record_job_execution("test_job", "success")
        record_job_execution("test_job", "failed")

    def test_record_job_duration_does_not_raise(self):
        record_job_duration("test_job", 1.23)
        record_job_duration("test_job", 0.0)

    def test_record_items_processed_does_not_raise(self):
        record_items_processed("test_job", "success", count=5)
        record_items_processed("test_job", "failed")

    def test_record_renewal_attempt_does_not_raise(self):
        record_renewal_attempt("success")
        record_renewal_attempt("failed")

    def test_record_payment_failure_does_not_raise(self):
        record_payment_failure("insufficient_funds")
        record_payment_failure("timeout")

    def test_record_renewal_skipped_does_not_raise(self):
        record_renewal_skipped("canceled")
        record_renewal_skipped("no_recurring_token")
        record_renewal_skipped("paddle_managed")
        record_renewal_skipped("invalid_amount")
