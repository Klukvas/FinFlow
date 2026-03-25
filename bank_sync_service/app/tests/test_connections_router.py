"""Tests for app/routers/connections.py - Connections API endpoints."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

from app.tests.conftest import TEST_WORKSPACE_ID, TEST_WORKSPACE_ID_HEADER, TEST_USER_ID


class TestConnectBank:
    """Tests for POST /connections/"""

    def test_connect_bank_success(self, client: TestClient, db):
        mock_connection = MagicMock()
        mock_connection.id = 1
        mock_connection.bank_type = "monobank"
        mock_connection.client_name = "Test User"
        mock_connection.is_active = True
        mock_connection.last_sync_at = None
        mock_connection.created_at = None
        mock_connection.linked_accounts = []

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.connect = AsyncMock(return_value=mock_connection)

            response = client.post(
                "/connections/",
                json={"token": "valid-monobank-token"},
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == 1
        assert data["bank_type"] == "monobank"
        assert data["client_name"] == "Test User"
        assert data["is_active"] is True
        assert data["accounts"] == []

    def test_connect_bank_with_accounts(self, client: TestClient, db):
        mock_account = MagicMock()
        mock_account.id = 10
        mock_account.external_account_id = "ext_acc"
        mock_account.account_name = "UAH (black)"
        mock_account.currency = "UAH"
        mock_account.currency_code = 980
        mock_account.masked_pan = "*1234"
        mock_account.iban = "UA123"
        mock_account.finflow_account_id = None
        mock_account.is_synced = True

        mock_connection = MagicMock()
        mock_connection.id = 1
        mock_connection.bank_type = "monobank"
        mock_connection.client_name = "Test User"
        mock_connection.is_active = True
        mock_connection.last_sync_at = None
        mock_connection.created_at = None
        mock_connection.linked_accounts = [mock_account]

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.connect = AsyncMock(return_value=mock_connection)

            response = client.post(
                "/connections/",
                json={"token": "valid-monobank-token"},
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["accounts"]) == 1
        assert data["accounts"][0]["external_account_id"] == "ext_acc"

    def test_connect_bank_empty_token_rejected(self, client: TestClient):
        response = client.post(
            "/connections/",
            json={"token": ""},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_connect_bank_missing_token_rejected(self, client: TestClient):
        response = client.post(
            "/connections/",
            json={},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_connect_bank_token_validation_error(self, client: TestClient, db):
        from app.exceptions import TokenValidationError

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.connect = AsyncMock(side_effect=TokenValidationError("Bad token"))

            response = client.post(
                "/connections/",
                json={"token": "invalid-token"},
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "TOKEN_VALIDATION_FAILED" in response.json().get("errorCode", "")

    def test_connect_bank_rate_limit_error(self, client: TestClient, db):
        from app.exceptions import RateLimitError

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.connect = AsyncMock(side_effect=RateLimitError(45))

            response = client.post(
                "/connections/",
                json={"token": "valid-token"},
            )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_connect_bank_monobank_api_error(self, client: TestClient, db):
        from app.exceptions import MonobankApiError

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.connect = AsyncMock(side_effect=MonobankApiError("API down"))

            response = client.post(
                "/connections/",
                json={"token": "valid-token"},
            )

        assert response.status_code == status.HTTP_502_BAD_GATEWAY


class TestListConnections:
    """Tests for GET /connections/"""

    def test_list_connections_empty(self, client: TestClient, db):
        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.get_connections = MagicMock(return_value=[])

            response = client.get("/connections/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_connections_with_data(self, client: TestClient, db):
        mock_conn = MagicMock()
        mock_conn.id = 1
        mock_conn.bank_type = "monobank"
        mock_conn.client_name = "User A"
        mock_conn.is_active = True
        mock_conn.last_sync_at = None
        mock_conn.created_at = None
        mock_conn.linked_accounts = []

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.get_connections = MagicMock(return_value=[mock_conn])

            response = client.get("/connections/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["bank_type"] == "monobank"


class TestDisconnectBank:
    """Tests for DELETE /connections/{connection_id}"""

    def test_disconnect_success(self, client: TestClient, db):
        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.disconnect = MagicMock(return_value=None)

            response = client.delete("/connections/1")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_disconnect_not_found(self, client: TestClient, db):
        from app.exceptions import ConnectionNotFoundError

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.disconnect = MagicMock(
                side_effect=ConnectionNotFoundError(999)
            )

            response = client.delete("/connections/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_disconnect_sync_in_progress(self, client: TestClient, db):
        from app.exceptions import SyncInProgressError

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.disconnect = MagicMock(
                side_effect=SyncInProgressError(1)
            )

            response = client.delete("/connections/1")

        assert response.status_code == status.HTTP_409_CONFLICT


class TestLinkAccount:
    """Tests for PUT /connections/{connection_id}/accounts/{linked_account_id}/link"""

    def test_link_account_success(self, client: TestClient, db):
        mock_linked = MagicMock()
        mock_linked.id = 10
        mock_linked.external_account_id = "ext1"
        mock_linked.account_name = "UAH Card"
        mock_linked.currency = "UAH"
        mock_linked.currency_code = 980
        mock_linked.masked_pan = None
        mock_linked.iban = None
        mock_linked.finflow_account_id = 5
        mock_linked.is_synced = True

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.link_account = MagicMock(return_value=mock_linked)

            response = client.put(
                "/connections/1/accounts/10/link",
                json={"finflow_account_id": 5},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["finflow_account_id"] == 5

    def test_link_account_connection_not_found(self, client: TestClient, db):
        from app.exceptions import ConnectionNotFoundError

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.link_account = MagicMock(
                side_effect=ConnectionNotFoundError(999)
            )

            response = client.put(
                "/connections/999/accounts/10/link",
                json={"finflow_account_id": 5},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_link_account_linked_account_not_found(self, client: TestClient, db):
        from app.exceptions import LinkedAccountNotFoundError

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.link_account = MagicMock(
                side_effect=LinkedAccountNotFoundError(999)
            )

            response = client.put(
                "/connections/1/accounts/999/link",
                json={"finflow_account_id": 5},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_link_account_missing_body(self, client: TestClient):
        response = client.put(
            "/connections/1/accounts/10/link",
            json={},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestToggleAccountSync:
    """Tests for PUT /connections/{connection_id}/accounts/{linked_account_id}/toggle"""

    def test_toggle_sync_success(self, client: TestClient, db):
        mock_linked = MagicMock()
        mock_linked.id = 10
        mock_linked.external_account_id = "ext1"
        mock_linked.account_name = "UAH Card"
        mock_linked.currency = "UAH"
        mock_linked.currency_code = 980
        mock_linked.masked_pan = None
        mock_linked.iban = None
        mock_linked.finflow_account_id = 5
        mock_linked.is_synced = False

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.toggle_account_sync = MagicMock(return_value=mock_linked)

            response = client.put(
                "/connections/1/accounts/10/toggle",
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_synced"] is False

    def test_toggle_sync_not_found(self, client: TestClient, db):
        from app.exceptions import LinkedAccountNotFoundError

        with patch(
            "app.routers.connections.SyncService"
        ) as MockService:
            instance = MockService.return_value
            instance.toggle_account_sync = MagicMock(
                side_effect=LinkedAccountNotFoundError(999)
            )

            response = client.put(
                "/connections/1/accounts/999/toggle",
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
