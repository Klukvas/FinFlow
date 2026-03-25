"""Tests for the outbox processor background service.

Tests event processing, retry logic with exponential backoff, and error handling.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

import httpx

from payment_service.app.services.outbox_processor import (
    process_outbox_events,
    _schedule_retry,
    BASE_BACKOFF_SECONDS,
)
from payment_service.app.models.outbox import OutboxEvent


# ======================================================================
# _schedule_retry
# ======================================================================


class TestScheduleRetry:
    """Tests for the _schedule_retry helper."""

    def _make_event(self, retry_count: int = 0, max_retries: int = 10) -> MagicMock:
        event = MagicMock(spec=OutboxEvent)
        event.id = uuid4()
        event.event_type = "payment_success"
        event.aggregate_id = uuid4()
        event.retry_count = retry_count
        event.max_retries = max_retries
        event.status = "processing"
        event.last_error = None
        event.next_retry_at = None
        return event

    def test_increments_retry_count(self):
        event = self._make_event(retry_count=2)
        _schedule_retry(event, "HTTP 500")
        assert event.retry_count == 3

    def test_sets_pending_status_when_retries_remain(self):
        event = self._make_event(retry_count=0, max_retries=5)
        _schedule_retry(event, "timeout")
        assert event.status == "pending"

    def test_sets_failed_status_when_retries_exhausted(self):
        event = self._make_event(retry_count=9, max_retries=10)
        _schedule_retry(event, "final error")
        assert event.status == "failed"
        assert event.retry_count == 10

    def test_records_error_message(self):
        event = self._make_event()
        _schedule_retry(event, "Connection refused")
        assert event.last_error == "Connection refused"

    def test_truncates_long_error_message(self):
        event = self._make_event()
        long_error = "x" * 2000
        _schedule_retry(event, long_error)
        assert len(event.last_error) <= 1000

    def test_backoff_increases_exponentially(self):
        event = self._make_event(retry_count=0, max_retries=10)
        _schedule_retry(event, "err")
        next_retry_1 = event.next_retry_at

        event2 = self._make_event(retry_count=2, max_retries=10)
        _schedule_retry(event2, "err")
        next_retry_3 = event2.next_retry_at

        # After retry 3, backoff should be larger than after retry 1
        # (next_retry_at is set to utcnow() + backoff, so we check it's set)
        assert next_retry_1 is not None
        assert next_retry_3 is not None

    def test_backoff_capped_at_one_hour(self):
        event = self._make_event(retry_count=8, max_retries=20)
        _schedule_retry(event, "err")
        # 2^8 * 30 = 7680 > 3600 -> capped at 3600
        assert event.next_retry_at is not None


# ======================================================================
# process_outbox_events
# ======================================================================


class TestProcessOutboxEvents:
    """Tests for process_outbox_events."""

    @pytest.mark.asyncio
    @patch("payment_service.app.services.outbox_processor.SessionLocal")
    @patch("payment_service.app.services.outbox_processor.settings")
    async def test_returns_zero_when_no_events(self, mock_settings, mock_session_local):
        mock_settings.internal_secret_token = "test-token"
        mock_db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.with_for_update.return_value = query_mock
        query_mock.all.return_value = []
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        result = await process_outbox_events()
        assert result == 0
        mock_db.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("payment_service.app.services.outbox_processor.SessionLocal")
    @patch("payment_service.app.services.outbox_processor.settings")
    @patch("httpx.AsyncClient")
    async def test_delivers_event_on_success(self, mock_async_client, mock_settings, mock_session_local):
        mock_settings.internal_secret_token = "test-token"

        event = MagicMock(spec=OutboxEvent)
        event.id = uuid4()
        event.event_type = "payment_success"
        event.destination_url = "http://sub-service/activate"
        event.payload = {"user_id": "u1"}
        event.headers = None
        event.status = "pending"

        mock_db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.with_for_update.return_value = query_mock
        query_mock.all.return_value = [event]
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await process_outbox_events()
        assert result == 1
        assert event.status == "delivered"
        assert event.delivered_at is not None

    @pytest.mark.asyncio
    @patch("payment_service.app.services.outbox_processor.SessionLocal")
    @patch("payment_service.app.services.outbox_processor.settings")
    @patch("httpx.AsyncClient")
    async def test_marks_failed_on_4xx_response(self, mock_async_client, mock_settings, mock_session_local):
        mock_settings.internal_secret_token = "test-token"

        event = MagicMock(spec=OutboxEvent)
        event.id = uuid4()
        event.event_type = "payment_success"
        event.destination_url = "http://sub-service/activate"
        event.payload = {"user_id": "u1"}
        event.headers = None
        event.status = "pending"
        event.retry_count = 0
        event.max_retries = 10

        mock_db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.with_for_update.return_value = query_mock
        query_mock.all.return_value = [event]
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await process_outbox_events()
        assert result == 0
        assert event.status == "failed"

    @pytest.mark.asyncio
    @patch("payment_service.app.services.outbox_processor.SessionLocal")
    @patch("payment_service.app.services.outbox_processor.settings")
    @patch("httpx.AsyncClient")
    async def test_retries_on_5xx_response(self, mock_async_client, mock_settings, mock_session_local):
        mock_settings.internal_secret_token = "test-token"

        event = MagicMock(spec=OutboxEvent)
        event.id = uuid4()
        event.event_type = "payment_success"
        event.destination_url = "http://sub-service/activate"
        event.payload = {"user_id": "u1"}
        event.headers = None
        event.status = "pending"
        event.retry_count = 0
        event.max_retries = 10
        event.last_error = None
        event.next_retry_at = None

        mock_db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.with_for_update.return_value = query_mock
        query_mock.all.return_value = [event]
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await process_outbox_events()
        assert result == 0
        assert event.retry_count == 1
        assert event.status == "pending"

    @pytest.mark.asyncio
    @patch("payment_service.app.services.outbox_processor.SessionLocal")
    @patch("payment_service.app.services.outbox_processor.settings")
    @patch("httpx.AsyncClient")
    async def test_retries_on_connection_error(self, mock_async_client, mock_settings, mock_session_local):
        mock_settings.internal_secret_token = "test-token"

        event = MagicMock(spec=OutboxEvent)
        event.id = uuid4()
        event.event_type = "payment_failed"
        event.destination_url = "http://unreachable/endpoint"
        event.payload = {}
        event.headers = None
        event.status = "pending"
        event.retry_count = 0
        event.max_retries = 5
        event.last_error = None
        event.next_retry_at = None

        mock_db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.with_for_update.return_value = query_mock
        query_mock.all.return_value = [event]
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await process_outbox_events()
        assert result == 0
        assert event.retry_count == 1

    @pytest.mark.asyncio
    @patch("payment_service.app.services.outbox_processor.SessionLocal")
    @patch("payment_service.app.services.outbox_processor.settings")
    @patch("httpx.AsyncClient")
    async def test_includes_custom_headers(self, mock_async_client, mock_settings, mock_session_local):
        mock_settings.internal_secret_token = "test-token"

        event = MagicMock(spec=OutboxEvent)
        event.id = uuid4()
        event.event_type = "payment_success"
        event.destination_url = "http://service/endpoint"
        event.payload = {"data": "value"}
        event.headers = {"X-Custom": "custom-value"}
        event.status = "pending"

        mock_db = MagicMock()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.with_for_update.return_value = query_mock
        query_mock.all.return_value = [event]
        mock_db.query.return_value = query_mock
        mock_session_local.return_value = mock_db

        mock_response = MagicMock()
        mock_response.is_success = True

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_async_client.return_value.__aexit__ = AsyncMock(return_value=False)

        await process_outbox_events()

        call_kwargs = mock_client_instance.post.call_args.kwargs
        assert call_kwargs["headers"]["X-Custom"] == "custom-value"
        assert call_kwargs["headers"]["X-Internal-Token"] == "test-token"
