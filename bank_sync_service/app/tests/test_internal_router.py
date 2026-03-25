"""Tests for app/routers/internal.py - internal API endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime, timezone

from app.tests.conftest import INTERNAL_HEADERS, TEST_USER_ID


class TestInternalHealth:
    """Tests for GET /internal/health"""

    def test_internal_health_returns_ok(self, client: TestClient):
        response = client.get("/internal/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "bank-sync-service"


class TestGetUserConnections:
    """Tests for GET /internal/connections/user/{user_id}"""

    def test_missing_internal_token_returns_403(self, client: TestClient):
        response = client.get("/internal/connections/user/1")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_internal_token_returns_403(self, client: TestClient):
        response = client.get(
            "/internal/connections/user/1",
            headers={"X-Internal-Token": "wrong-token"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_connections_empty(self, client: TestClient, db):
        response = client.get(
            "/internal/connections/user/1",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_user_connections_with_data(self, client: TestClient, db):
        from app.models.bank_connection import BankConnection
        from app.tests.conftest import TEST_WORKSPACE_ID

        connection = BankConnection(
            user_id=42,
            workspace_id=TEST_WORKSPACE_ID,
            bank_type="monobank",
            encrypted_token="encrypted-token-value",
            client_name="Test User",
            is_active=True,
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)

        response = client.get(
            "/internal/connections/user/42",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["bank_type"] == "monobank"
        assert data[0]["is_active"] is True

    def test_get_user_connections_excludes_inactive(self, client: TestClient, db):
        from app.models.bank_connection import BankConnection
        from app.tests.conftest import TEST_WORKSPACE_ID

        active_conn = BankConnection(
            user_id=43,
            workspace_id=TEST_WORKSPACE_ID,
            bank_type="monobank",
            encrypted_token="token1",
            is_active=True,
        )
        inactive_conn = BankConnection(
            user_id=43,
            workspace_id=TEST_WORKSPACE_ID,
            bank_type="monobank",
            encrypted_token="token2",
            is_active=False,
        )
        db.add(active_conn)
        db.add(inactive_conn)
        db.commit()

        response = client.get(
            "/internal/connections/user/43",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_active"] is True

    def test_get_user_connections_different_user_returns_empty(
        self, client: TestClient, db
    ):
        from app.models.bank_connection import BankConnection
        from app.tests.conftest import TEST_WORKSPACE_ID

        connection = BankConnection(
            user_id=100,
            workspace_id=TEST_WORKSPACE_ID,
            bank_type="monobank",
            encrypted_token="token",
            is_active=True,
        )
        db.add(connection)
        db.commit()

        response = client.get(
            "/internal/connections/user/999",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_user_connections_with_last_sync_at(self, client: TestClient, db):
        from app.models.bank_connection import BankConnection
        from app.tests.conftest import TEST_WORKSPACE_ID

        now = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        connection = BankConnection(
            user_id=44,
            workspace_id=TEST_WORKSPACE_ID,
            bank_type="monobank",
            encrypted_token="token",
            is_active=True,
            last_sync_at=now,
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)

        response = client.get(
            "/internal/connections/user/44",
            headers=INTERNAL_HEADERS,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["last_sync_at"] is not None
