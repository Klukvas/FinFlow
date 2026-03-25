"""
Tests for PDFUploadRepository.

Covers:
- get_monthly_upload_count: current month counting
- create_upload_record: record creation with all fields
- get_upload_history: pagination and ordering
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.repositories.pdf_upload_repository import PDFUploadRepository
from app.models.pdf_upload import PDFUpload


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return PDFUploadRepository(mock_db)


class TestGetMonthlyUploadCount:

    def test_returns_count(self, repo, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3

        result = repo.get_monthly_upload_count(42)

        assert result == 3
        mock_db.query.assert_called_once_with(PDFUpload)

    def test_returns_zero_for_no_uploads(self, repo, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0

        result = repo.get_monthly_upload_count(42)

        assert result == 0


class TestCreateUploadRecord:

    def test_creates_record_with_all_fields(self, repo, mock_db):
        mock_db.refresh = MagicMock()

        result = repo.create_upload_record(
            user_id=42,
            filename="statement.pdf",
            file_size=1024,
            total_transactions=10,
            successful_parses=8,
            failed_parses=2,
            status="success",
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        created = mock_db.add.call_args[0][0]
        assert created.user_id == 42
        assert created.filename == "statement.pdf"
        assert created.file_size == 1024
        assert created.total_transactions == 10
        assert created.successful_parses == 8
        assert created.failed_parses == 2
        assert created.status == "success"

    def test_creates_record_with_defaults(self, repo, mock_db):
        mock_db.refresh = MagicMock()

        repo.create_upload_record(user_id=42)

        created = mock_db.add.call_args[0][0]
        assert created.user_id == 42
        assert created.filename is None
        assert created.file_size is None
        assert created.total_transactions == 0
        assert created.successful_parses == 0
        assert created.failed_parses == 0
        assert created.status == "success"

    def test_creates_failed_record(self, repo, mock_db):
        mock_db.refresh = MagicMock()

        repo.create_upload_record(
            user_id=42,
            filename="bad.pdf",
            status="failed",
        )

        created = mock_db.add.call_args[0][0]
        assert created.status == "failed"


class TestGetUploadHistory:

    def test_returns_paginated_results(self, repo, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [MagicMock(), MagicMock()]

        result = repo.get_upload_history(42, limit=10, offset=0)

        assert len(result) == 2
        mock_query.limit.assert_called_once_with(10)
        mock_query.offset.assert_called_once_with(0)

    def test_default_pagination(self, repo, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = []

        repo.get_upload_history(42)

        mock_query.limit.assert_called_once_with(50)
        mock_query.offset.assert_called_once_with(0)
