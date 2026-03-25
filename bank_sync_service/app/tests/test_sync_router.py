"""Tests for app/routers/sync.py - Sync API endpoints."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime, timezone

from app.tests.conftest import TEST_WORKSPACE_ID, TEST_WORKSPACE_ID_HEADER, TEST_USER_ID


class TestTriggerSync:
    """Tests for POST /connections/{connection_id}/sync"""

    def test_trigger_sync_success(self, client: TestClient, db):
        mock_sync_log = MagicMock()
        mock_sync_log.id = 1
        mock_sync_log.status = "completed"
        mock_sync_log.transactions_found = 10
        mock_sync_log.transactions_imported = 8
        mock_sync_log.transactions_skipped = 2
        mock_sync_log.error_message = None
        mock_sync_log.sync_from = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_sync_log.sync_to = datetime(2024, 1, 31, tzinfo=timezone.utc)
        mock_sync_log.started_at = datetime(2024, 1, 31, tzinfo=timezone.utc)
        mock_sync_log.completed_at = datetime(2024, 1, 31, tzinfo=timezone.utc)

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.sync_connection = AsyncMock(return_value=mock_sync_log)

            response = client.post(
                "/connections/1/sync",
                json={"days_back": 7},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["transactions_found"] == 10
        assert data["transactions_imported"] == 8

    def test_trigger_sync_default_body(self, client: TestClient, db):
        mock_sync_log = MagicMock()
        mock_sync_log.id = 1
        mock_sync_log.status = "completed"
        mock_sync_log.transactions_found = 0
        mock_sync_log.transactions_imported = 0
        mock_sync_log.transactions_skipped = 0
        mock_sync_log.error_message = None
        mock_sync_log.sync_from = None
        mock_sync_log.sync_to = None
        mock_sync_log.started_at = None
        mock_sync_log.completed_at = None

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.sync_connection = AsyncMock(return_value=mock_sync_log)

            response = client.post("/connections/1/sync")

        assert response.status_code == status.HTTP_200_OK

    def test_trigger_sync_connection_not_found(self, client: TestClient, db):
        from app.exceptions import ConnectionNotFoundError

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.sync_connection = AsyncMock(
                side_effect=ConnectionNotFoundError(999)
            )

            response = client.post("/connections/999/sync")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_trigger_sync_rate_limit(self, client: TestClient, db):
        from app.exceptions import RateLimitError

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.sync_connection = AsyncMock(
                side_effect=RateLimitError(30)
            )

            response = client.post("/connections/1/sync")

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_trigger_sync_already_in_progress(self, client: TestClient, db):
        from app.exceptions import SyncInProgressError

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.sync_connection = AsyncMock(
                side_effect=SyncInProgressError(1)
            )

            response = client.post("/connections/1/sync")

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_trigger_sync_invalid_days_back(self, client: TestClient):
        response = client.post(
            "/connections/1/sync",
            json={"days_back": 0},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_trigger_sync_days_back_too_high(self, client: TestClient):
        response = client.post(
            "/connections/1/sync",
            json={"days_back": 31},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPreviewSync:
    """Tests for POST /connections/{connection_id}/sync/preview"""

    def test_preview_sync_success(self, client: TestClient, db):
        preview_result = {
            "transactions": [
                {
                    "external_id": "tx1",
                    "type": "expense",
                    "amount": "50.00",
                    "currency": "UAH",
                    "date": "2024-01-15",
                    "description": "Shop",
                    "mcc": 5411,
                    "category_id": None,
                    "category_name": None,
                    "account_id": 1,
                }
            ],
            "total_found": 5,
            "total_new": 1,
            "total_skipped": 4,
        }

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.preview_sync = AsyncMock(return_value=preview_result)

            response = client.post("/connections/1/sync/preview")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_found"] == 5
        assert data["total_new"] == 1
        assert len(data["transactions"]) == 1

    def test_preview_sync_connection_not_found(self, client: TestClient, db):
        from app.exceptions import ConnectionNotFoundError

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.preview_sync = AsyncMock(
                side_effect=ConnectionNotFoundError(999)
            )

            response = client.post("/connections/999/sync/preview")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_preview_sync_rate_limit(self, client: TestClient, db):
        from app.exceptions import RateLimitError

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.preview_sync = AsyncMock(
                side_effect=RateLimitError(60)
            )

            response = client.post("/connections/1/sync/preview")

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestConfirmSync:
    """Tests for POST /connections/{connection_id}/sync/confirm"""

    def test_confirm_sync_success(self, client: TestClient, db):
        mock_sync_log = MagicMock()
        mock_sync_log.id = 2
        mock_sync_log.status = "completed"
        mock_sync_log.transactions_found = 3
        mock_sync_log.transactions_imported = 3
        mock_sync_log.transactions_skipped = 0
        mock_sync_log.error_message = None
        mock_sync_log.sync_from = None
        mock_sync_log.sync_to = None
        mock_sync_log.started_at = None
        mock_sync_log.completed_at = None

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.confirm_sync = AsyncMock(return_value=mock_sync_log)

            response = client.post(
                "/connections/1/sync/confirm",
                json={
                    "days_back": 7,
                    "transactions": [
                        {
                            "external_id": "tx1",
                            "type": "expense",
                            "amount": "50.00",
                            "currency": "UAH",
                            "date": "2024-01-15",
                            "description": "Shop",
                            "account_id": 1,
                        }
                    ],
                },
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert data["transactions_imported"] == 3

    def test_confirm_sync_connection_not_found(self, client: TestClient, db):
        from app.exceptions import ConnectionNotFoundError

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.confirm_sync = AsyncMock(
                side_effect=ConnectionNotFoundError(999)
            )

            response = client.post(
                "/connections/999/sync/confirm",
                json={"transactions": [], "days_back": 7},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_confirm_sync_missing_transactions(self, client: TestClient):
        response = client.post(
            "/connections/1/sync/confirm",
            json={"days_back": 7},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_confirm_sync_invalid_transaction_data(self, client: TestClient):
        response = client.post(
            "/connections/1/sync/confirm",
            json={
                "transactions": [
                    {
                        "external_id": "tx1",
                        # Missing required fields
                    }
                ],
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetSyncStatus:
    """Tests for GET /connections/{connection_id}/sync/status"""

    def test_get_sync_status_found(self, client: TestClient, db):
        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.status = "completed"
        mock_log.transactions_found = 5
        mock_log.transactions_imported = 5
        mock_log.transactions_skipped = 0
        mock_log.error_message = None
        mock_log.sync_from = None
        mock_log.sync_to = None
        mock_log.started_at = None
        mock_log.completed_at = None

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.get_sync_status = MagicMock(return_value=mock_log)

            response = client.get("/connections/1/sync/status")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "completed"

    def test_get_sync_status_none(self, client: TestClient, db):
        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.get_sync_status = MagicMock(return_value=None)

            response = client.get("/connections/1/sync/status")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() is None

    def test_get_sync_status_connection_not_found(self, client: TestClient, db):
        from app.exceptions import ConnectionNotFoundError

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.get_sync_status = MagicMock(
                side_effect=ConnectionNotFoundError(999)
            )

            response = client.get("/connections/999/sync/status")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetSyncHistory:
    """Tests for GET /connections/{connection_id}/sync/history"""

    def test_get_sync_history_empty(self, client: TestClient, db):
        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.get_sync_history = MagicMock(return_value=[])

            response = client.get("/connections/1/sync/history")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_sync_history_with_entries(self, client: TestClient, db):
        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.status = "completed"
        mock_log.transactions_found = 3
        mock_log.transactions_imported = 3
        mock_log.transactions_skipped = 0
        mock_log.error_message = None
        mock_log.sync_from = None
        mock_log.sync_to = None
        mock_log.started_at = None
        mock_log.completed_at = None

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.get_sync_history = MagicMock(return_value=[mock_log])

            response = client.get("/connections/1/sync/history")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1

    def test_get_sync_history_with_pagination(self, client: TestClient, db):
        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.get_sync_history = MagicMock(return_value=[])

            response = client.get("/connections/1/sync/history?skip=5&limit=10")

        assert response.status_code == status.HTTP_200_OK
        instance.get_sync_history.assert_called_once()
        call_args = instance.get_sync_history.call_args
        assert call_args[0][3] == 5   # skip
        assert call_args[0][4] == 10  # limit

    def test_get_sync_history_invalid_skip(self, client: TestClient):
        response = client.get("/connections/1/sync/history?skip=-1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_sync_history_limit_too_high(self, client: TestClient):
        response = client.get("/connections/1/sync/history?limit=101")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_sync_history_limit_zero(self, client: TestClient):
        response = client.get("/connections/1/sync/history?limit=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_sync_history_connection_not_found(self, client: TestClient, db):
        from app.exceptions import ConnectionNotFoundError

        with patch("app.routers.sync.SyncService") as MockService:
            instance = MockService.return_value
            instance.get_sync_history = MagicMock(
                side_effect=ConnectionNotFoundError(999)
            )

            response = client.get("/connections/999/sync/history")

        assert response.status_code == status.HTTP_404_NOT_FOUND
