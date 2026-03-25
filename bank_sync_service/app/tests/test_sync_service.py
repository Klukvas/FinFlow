"""Tests for app/services/sync_service.py - SyncService business logic."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock
from datetime import datetime, timedelta, timezone
from uuid import UUID
from decimal import Decimal

from app.services.sync_service import SyncService, _utcnow
from app.models.bank_connection import BankConnection
from app.models.linked_account import LinkedAccount
from app.models.sync_log import SyncLog
from app.models.synced_transaction import SyncedTransaction
from app.exceptions import (
    ConnectionNotFoundError,
    LinkedAccountNotFoundError,
    RateLimitError,
    SyncInProgressError,
    TokenValidationError,
    TransactionLimitExceededError,
)
from app.schemas.monobank import MonobankClientInfo, MonobankAccount, MonobankStatementItem


TEST_WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TEST_USER_ID = 42


def _make_mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.query.return_value = db
    db.filter.return_value = db
    db.order_by.return_value = db
    db.offset.return_value = db
    db.limit.return_value = db
    return db


def _make_connection(**overrides):
    """Create a mock BankConnection."""
    conn = MagicMock(spec=BankConnection)
    conn.id = overrides.get("id", 1)
    conn.user_id = overrides.get("user_id", TEST_USER_ID)
    conn.workspace_id = overrides.get("workspace_id", TEST_WORKSPACE_ID)
    conn.bank_type = overrides.get("bank_type", "monobank")
    conn.encrypted_token = overrides.get("encrypted_token", "encrypted")
    conn.client_name = overrides.get("client_name", "Test User")
    conn.is_active = overrides.get("is_active", True)
    conn.last_sync_at = overrides.get("last_sync_at", None)
    conn.linked_accounts = overrides.get("linked_accounts", [])
    return conn


def _make_linked_account(**overrides):
    """Create a mock LinkedAccount."""
    acc = MagicMock(spec=LinkedAccount)
    acc.id = overrides.get("id", 10)
    acc.connection_id = overrides.get("connection_id", 1)
    acc.external_account_id = overrides.get("external_account_id", "ext_acc_1")
    acc.finflow_account_id = overrides.get("finflow_account_id", 5)
    acc.account_name = overrides.get("account_name", "UAH (black)")
    acc.currency = overrides.get("currency", "UAH")
    acc.currency_code = overrides.get("currency_code", 980)
    acc.is_synced = overrides.get("is_synced", True)
    return acc


class TestSyncServiceGetConnections:
    """Tests for SyncService.get_connections."""

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_get_connections_returns_list(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        db.all.return_value = [conn]

        service = SyncService(db)
        result = service.get_connections(TEST_USER_ID, TEST_WORKSPACE_ID)

        assert len(result) == 1

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_get_connections_empty(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        db.all.return_value = []

        service = SyncService(db)
        result = service.get_connections(TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result == []


class TestSyncServiceGetConnection:
    """Tests for SyncService.get_connection."""

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_get_connection_found(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        db.first.return_value = conn

        service = SyncService(db)
        result = service.get_connection(1, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.id == 1

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_get_connection_not_found_raises(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        db.first.return_value = None

        service = SyncService(db)

        with pytest.raises(ConnectionNotFoundError):
            service.get_connection(999, TEST_USER_ID, TEST_WORKSPACE_ID)


class TestSyncServiceDisconnect:
    """Tests for SyncService.disconnect."""

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_disconnect_success(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()

        # get_connection call returns conn
        db.first.side_effect = [conn, None]  # connection found, no active sync

        service = SyncService(db)
        service.disconnect(1, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert conn.is_active is False
        db.commit.assert_called()

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_disconnect_with_active_sync_raises(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        active_log = MagicMock(spec=SyncLog)

        # First filter for get_connection, second for active sync check
        db.first.side_effect = [conn, active_log]

        service = SyncService(db)

        with pytest.raises(SyncInProgressError):
            service.disconnect(1, TEST_USER_ID, TEST_WORKSPACE_ID)


class TestSyncServiceLinkAccount:
    """Tests for SyncService.link_account."""

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_link_account_success(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        linked = _make_linked_account(finflow_account_id=None)

        db.first.side_effect = [conn, linked]

        service = SyncService(db)
        result = service.link_account(1, 10, 5, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.finflow_account_id == 5
        db.commit.assert_called()

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_link_account_not_found_raises(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()

        db.first.side_effect = [conn, None]

        service = SyncService(db)

        with pytest.raises(LinkedAccountNotFoundError):
            service.link_account(1, 999, 5, TEST_USER_ID, TEST_WORKSPACE_ID)


class TestSyncServiceToggleAccountSync:
    """Tests for SyncService.toggle_account_sync."""

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_toggle_from_true_to_false(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        linked = _make_linked_account(is_synced=True)

        db.first.side_effect = [conn, linked]

        service = SyncService(db)
        result = service.toggle_account_sync(1, 10, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.is_synced is not True

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_toggle_not_found_raises(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()

        db.first.side_effect = [conn, None]

        service = SyncService(db)

        with pytest.raises(LinkedAccountNotFoundError):
            service.toggle_account_sync(1, 999, TEST_USER_ID, TEST_WORKSPACE_ID)


class TestSyncServiceEnforceRateLimit:
    """Tests for SyncService._enforce_rate_limit."""

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_no_last_sync_passes(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        service = SyncService(db)
        conn = _make_connection(last_sync_at=None)

        # Should not raise
        service._enforce_rate_limit(conn)

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_recent_sync_raises_rate_limit(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        service = SyncService(db)

        # Last sync 10 seconds ago
        conn = _make_connection(
            last_sync_at=datetime.now(timezone.utc) - timedelta(seconds=10)
        )

        with pytest.raises(RateLimitError):
            service._enforce_rate_limit(conn)

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_old_sync_passes(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        service = SyncService(db)

        conn = _make_connection(
            last_sync_at=datetime.now(timezone.utc) - timedelta(seconds=120)
        )

        # Should not raise
        service._enforce_rate_limit(conn)

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_rate_limit_with_naive_datetime(self, mock_ws):
        """If last_sync_at is naive (no tzinfo), the service adds UTC."""
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        service = SyncService(db)

        # Use a naive datetime that is recent
        naive_recent = datetime.utcnow() - timedelta(seconds=5)
        conn = _make_connection(last_sync_at=naive_recent)

        with pytest.raises(RateLimitError):
            service._enforce_rate_limit(conn)


class TestSyncServiceCheckNoActiveSync:
    """Tests for SyncService._check_no_active_sync."""

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_no_active_sync_passes(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        db.first.return_value = None

        service = SyncService(db)
        conn = _make_connection()

        # Should not raise
        service._check_no_active_sync(conn)

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_active_sync_raises(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        active_log = MagicMock(spec=SyncLog)
        db.first.return_value = active_log

        service = SyncService(db)
        conn = _make_connection()

        with pytest.raises(SyncInProgressError):
            service._check_no_active_sync(conn)


class TestSyncServiceGetLinkedAccounts:
    """Tests for SyncService._get_linked_accounts."""

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_returns_only_linked_accounts(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()

        linked_with_finflow = _make_linked_account(finflow_account_id=5)
        linked_without_finflow = _make_linked_account(id=11, finflow_account_id=None)
        db.all.return_value = [linked_with_finflow, linked_without_finflow]

        service = SyncService(db)
        conn = _make_connection()

        result = service._get_linked_accounts(conn)

        assert len(result) == 1
        assert result[0].finflow_account_id == 5

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_filters_by_account_ids(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()

        acc1 = _make_linked_account(id=10, finflow_account_id=5)
        db.all.return_value = [acc1]

        service = SyncService(db)
        conn = _make_connection()

        result = service._get_linked_accounts(conn, account_ids=[10])

        assert len(result) == 1

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_returns_empty_when_all_unlinked(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()

        unlinked = _make_linked_account(finflow_account_id=None)
        db.all.return_value = [unlinked]

        service = SyncService(db)
        conn = _make_connection()

        result = service._get_linked_accounts(conn)

        assert result == []


class TestSyncServiceGetSyncStatus:
    """Tests for SyncService.get_sync_status."""

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_returns_latest_sync_log(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        log = MagicMock(spec=SyncLog)
        log.status = "completed"

        # get_connection and then query for SyncLog
        db.first.side_effect = [conn, log]

        service = SyncService(db)
        result = service.get_sync_status(1, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.status == "completed"

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_returns_none_when_no_logs(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()

        db.first.side_effect = [conn, None]

        service = SyncService(db)
        result = service.get_sync_status(1, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result is None


class TestSyncServiceGetSyncHistory:
    """Tests for SyncService.get_sync_history."""

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_returns_paginated_logs(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        logs = [MagicMock(spec=SyncLog), MagicMock(spec=SyncLog)]

        db.first.return_value = conn
        db.all.return_value = logs

        service = SyncService(db)
        result = service.get_sync_history(1, TEST_USER_ID, TEST_WORKSPACE_ID, skip=0, limit=10)

        assert len(result) == 2

    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    def test_connection_not_found_raises(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        db.first.return_value = None

        service = SyncService(db)

        with pytest.raises(ConnectionNotFoundError):
            service.get_sync_history(999, TEST_USER_ID, TEST_WORKSPACE_ID)


class TestSyncServiceConnect:
    """Tests for SyncService.connect (async)."""

    @pytest.mark.asyncio
    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    async def test_connect_success(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()

        mock_client_info = MonobankClientInfo(
            name="User Name",
            clientId="cid123",
            accounts=[
                MonobankAccount(id="acc1", balance=10000, currencyCode=980),
            ],
        )

        with patch(
            "app.services.sync_service.monobank_client.get_client_info",
            new_callable=AsyncMock,
            return_value=mock_client_info,
        ), patch(
            "app.services.sync_service.encryption.encrypt",
            return_value="encrypted-token",
        ):
            service = SyncService(db)
            result = await service.connect(TEST_USER_ID, TEST_WORKSPACE_ID, "mono-token")

        db.add.assert_called()
        db.commit.assert_called()

    @pytest.mark.asyncio
    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    async def test_connect_invalid_token_raises(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()

        with patch(
            "app.services.sync_service.monobank_client.get_client_info",
            new_callable=AsyncMock,
            side_effect=Exception("Connection failed"),
        ):
            service = SyncService(db)

            with pytest.raises(TokenValidationError):
                await service.connect(TEST_USER_ID, TEST_WORKSPACE_ID, "bad-token")

    @pytest.mark.asyncio
    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    async def test_connect_rate_limit_propagates(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()

        with patch(
            "app.services.sync_service.monobank_client.get_client_info",
            new_callable=AsyncMock,
            side_effect=RateLimitError(30),
        ):
            service = SyncService(db)

            with pytest.raises(RateLimitError):
                await service.connect(TEST_USER_ID, TEST_WORKSPACE_ID, "token")


class TestSyncServiceConfirmSync:
    """Tests for SyncService.confirm_sync (async)."""

    @pytest.mark.asyncio
    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    async def test_confirm_sync_success(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        db.first.side_effect = [conn, None]  # connection found, no active sync

        # Make flush and refresh work with the mock SyncLog
        mock_sync_log = MagicMock(spec=SyncLog)
        mock_sync_log.id = 1
        mock_sync_log.status = "completed"
        mock_sync_log.transactions_found = 1
        mock_sync_log.transactions_imported = 1
        mock_sync_log.transactions_skipped = 0

        service = SyncService(db)

        with patch.object(
            service.expense_client, "create_expense",
            new_callable=AsyncMock,
            return_value={"id": 100},
        ):
            transactions = [
                {
                    "type": "expense",
                    "external_id": "tx1",
                    "amount": "50.00",
                    "currency": "UAH",
                    "date": "2024-01-15",
                    "description": "Shop",
                    "account_id": 1,
                },
            ]
            result = await service.confirm_sync(
                1, TEST_USER_ID, TEST_WORKSPACE_ID, transactions
            )

        db.commit.assert_called()

    @pytest.mark.asyncio
    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    async def test_confirm_sync_with_limit_exceeded(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        db.first.side_effect = [conn, None]

        service = SyncService(db)

        with patch.object(
            service.expense_client, "create_expense",
            new_callable=AsyncMock,
            side_effect=TransactionLimitExceededError("expense"),
        ):
            transactions = [
                {
                    "type": "expense",
                    "external_id": "tx1",
                    "amount": "50.00",
                    "currency": "UAH",
                    "date": "2024-01-15",
                    "description": "Shop",
                    "account_id": 1,
                },
                {
                    "type": "expense",
                    "external_id": "tx2",
                    "amount": "30.00",
                    "currency": "UAH",
                    "date": "2024-01-15",
                    "description": "Shop 2",
                    "account_id": 1,
                },
            ]
            result = await service.confirm_sync(
                1, TEST_USER_ID, TEST_WORKSPACE_ID, transactions
            )

        # The second transaction should be skipped due to the limit
        db.commit.assert_called()

    @pytest.mark.asyncio
    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    async def test_confirm_sync_income_transactions(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        db.first.side_effect = [conn, None]

        service = SyncService(db)

        with patch.object(
            service.income_client, "create_income",
            new_callable=AsyncMock,
            return_value={"id": 200},
        ):
            transactions = [
                {
                    "type": "income",
                    "external_id": "tx1",
                    "amount": "1000.00",
                    "currency": "UAH",
                    "date": "2024-01-15",
                    "description": "Salary",
                    "account_id": 1,
                },
            ]
            result = await service.confirm_sync(
                1, TEST_USER_ID, TEST_WORKSPACE_ID, transactions
            )

        db.commit.assert_called()

    @pytest.mark.asyncio
    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    async def test_confirm_sync_handles_create_failure(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        db.first.side_effect = [conn, None]

        service = SyncService(db)

        with patch.object(
            service.expense_client, "create_expense",
            new_callable=AsyncMock,
            side_effect=Exception("Service unavailable"),
        ):
            transactions = [
                {
                    "type": "expense",
                    "external_id": "tx1",
                    "amount": "50.00",
                    "currency": "UAH",
                    "date": "2024-01-15",
                    "description": "Shop",
                    "account_id": 1,
                },
            ]
            result = await service.confirm_sync(
                1, TEST_USER_ID, TEST_WORKSPACE_ID, transactions
            )

        # Should still commit (in finally block)
        db.commit.assert_called()

    @pytest.mark.asyncio
    @patch("shared.clients.workspace.WorkspaceClient.get_instance")
    async def test_confirm_sync_with_category_id(self, mock_ws):
        mock_ws.return_value = MagicMock(authorize=MagicMock(return_value=(True, "owner")))
        db = _make_mock_db()
        conn = _make_connection()
        db.first.side_effect = [conn, None]

        service = SyncService(db)

        with patch.object(
            service.expense_client, "create_expense",
            new_callable=AsyncMock,
            return_value={"id": 100},
        ) as mock_create:
            transactions = [
                {
                    "type": "expense",
                    "external_id": "tx1",
                    "amount": "50.00",
                    "currency": "UAH",
                    "date": "2024-01-15",
                    "description": "Shop",
                    "account_id": 1,
                    "category_id": 42,
                },
            ]
            await service.confirm_sync(
                1, TEST_USER_ID, TEST_WORKSPACE_ID, transactions
            )

        # The create_expense call should include category_id
        call_data = mock_create.call_args[0][0]
        assert call_data["category_id"] == 42
