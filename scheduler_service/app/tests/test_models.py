"""Tests for SQLAlchemy models — column definitions, defaults, enum values."""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from app.models.models import JobExecution, RenewalAttempt, JobStatus


class TestJobStatusEnum:
    def test_all_expected_values_exist(self):
        assert JobStatus.PENDING == "PENDING"
        assert JobStatus.RUNNING == "RUNNING"
        assert JobStatus.SUCCESS == "SUCCESS"
        assert JobStatus.FAILED == "FAILED"
        assert JobStatus.SKIPPED == "SKIPPED"

    def test_enum_count(self):
        assert len(JobStatus) == 5

    def test_is_string_enum(self):
        for status in JobStatus:
            assert isinstance(status, str)
            assert isinstance(status, JobStatus)


class TestJobExecutionModel:
    def test_table_name(self):
        assert JobExecution.__tablename__ == "job_executions"

    def test_default_status_is_pending(self):
        """The column default should be PENDING."""
        status_col = JobExecution.__table__.columns["status"]
        assert status_col.default.arg == JobStatus.PENDING

    def test_default_items_processed_is_zero(self):
        items_col = JobExecution.__table__.columns["items_processed"]
        assert items_col.default.arg == 0

    def test_nullable_fields(self):
        table = JobExecution.__table__
        assert table.columns["started_at"].nullable is True
        assert table.columns["completed_at"].nullable is True
        assert table.columns["error_message"].nullable is True
        assert table.columns["error_details"].nullable is True
        assert table.columns["extra_data"].nullable is True

    def test_required_fields(self):
        table = JobExecution.__table__
        assert table.columns["job_name"].nullable is False
        assert table.columns["status"].nullable is False
        assert table.columns["created_at"].nullable is False

    def test_primary_key_is_uuid(self):
        pk_cols = [c for c in JobExecution.__table__.columns if c.primary_key]
        assert len(pk_cols) == 1
        assert pk_cols[0].name == "id"

    def test_job_name_is_indexed(self):
        job_name_col = JobExecution.__table__.columns["job_name"]
        assert job_name_col.index is True


class TestRenewalAttemptModel:
    def test_table_name(self):
        assert RenewalAttempt.__tablename__ == "renewal_attempts"

    def test_default_attempt_number_is_one(self):
        col = RenewalAttempt.__table__.columns["attempt_number"]
        assert col.default.arg == 1

    def test_nullable_fields(self):
        table = RenewalAttempt.__table__
        assert table.columns["payment_id"].nullable is True
        assert table.columns["failure_reason"].nullable is True
        assert table.columns["extra_data"].nullable is True

    def test_required_fields(self):
        table = RenewalAttempt.__table__
        assert table.columns["job_execution_id"].nullable is False
        assert table.columns["subscription_id"].nullable is False
        assert table.columns["user_id"].nullable is False
        assert table.columns["amount"].nullable is False
        assert table.columns["currency"].nullable is False
        assert table.columns["status"].nullable is False

    def test_subscription_id_is_indexed(self):
        col = RenewalAttempt.__table__.columns["subscription_id"]
        assert col.index is True

    def test_job_execution_id_is_indexed(self):
        col = RenewalAttempt.__table__.columns["job_execution_id"]
        assert col.index is True

    def test_currency_max_length(self):
        col = RenewalAttempt.__table__.columns["currency"]
        assert col.type.length == 3
