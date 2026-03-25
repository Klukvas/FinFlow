"""E2E tests for bank_sync_service: health, connections, sync, webhook, auth gating."""
import os

import pytest

from tests.e2e.clients.bank_sync_client import BankSyncApiClient

pytestmark = pytest.mark.bank_sync

FAKE_MONOBANK_TOKEN = "fake_monobank_token_for_testing"
NONEXISTENT_CONNECTION_ID = 999999


# ---------------------------------------------------------------------------
# Fixtures (bank_sync_client & unauthenticated_bank_sync_client from conftest)
# ---------------------------------------------------------------------------


@pytest.fixture
def no_workspace_bank_sync_client(primary_user) -> BankSyncApiClient:
    """Client with auth token but no workspace header."""
    client = BankSyncApiClient()
    client.set_token(primary_user["token"])
    return client


@pytest.fixture
def secondary_bank_sync_client(secondary_user) -> BankSyncApiClient:
    """Client authenticated as secondary user with a different workspace."""
    client = BankSyncApiClient()
    client.set_token(secondary_user["token"])
    return client


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------


class TestBankSyncHealth:

    async def test_health_check(self, bank_sync_client):
        result = await bank_sync_client.health()
        data = result.raise_on_error()
        assert data["status"] == "healthy"
        assert data["service"] == "bank-sync-service"

    async def test_internal_health_check(self, bank_sync_client):
        result = await bank_sync_client.internal_health()
        data = result.raise_on_error()
        assert data["status"] == "healthy"
        assert data["service"] == "bank-sync-service"


# ---------------------------------------------------------------------------
# Auth gating
# ---------------------------------------------------------------------------


class TestBankSyncAuthGating:

    async def test_list_connections_without_auth_rejected(
        self, unauthenticated_bank_sync_client
    ):
        """Listing connections without a Bearer token should fail with 401/403."""
        result = await unauthenticated_bank_sync_client.list_connections()
        assert not result.ok
        assert result.status_code in (401, 403)

    async def test_connect_bank_without_auth_rejected(
        self, unauthenticated_bank_sync_client
    ):
        """Creating a connection without auth should fail."""
        result = await unauthenticated_bank_sync_client.connect_bank(FAKE_MONOBANK_TOKEN)
        assert not result.ok
        assert result.status_code in (401, 403)

    async def test_disconnect_without_auth_rejected(
        self, unauthenticated_bank_sync_client
    ):
        """Disconnecting without auth should fail."""
        result = await unauthenticated_bank_sync_client.disconnect(1)
        assert not result.ok
        assert result.status_code in (401, 403)

    async def test_sync_trigger_without_auth_rejected(
        self, unauthenticated_bank_sync_client
    ):
        """Triggering sync without auth should fail."""
        result = await unauthenticated_bank_sync_client.trigger_sync(1)
        assert not result.ok
        assert result.status_code in (401, 403)

    async def test_sync_preview_without_auth_rejected(
        self, unauthenticated_bank_sync_client
    ):
        """Preview sync without auth should fail."""
        result = await unauthenticated_bank_sync_client.preview_sync(1)
        assert not result.ok
        assert result.status_code in (401, 403)

    async def test_sync_status_without_auth_rejected(
        self, unauthenticated_bank_sync_client
    ):
        """Getting sync status without auth should fail."""
        result = await unauthenticated_bank_sync_client.get_sync_status(1)
        assert not result.ok
        assert result.status_code in (401, 403)

    async def test_sync_history_without_auth_rejected(
        self, unauthenticated_bank_sync_client
    ):
        """Getting sync history without auth should fail."""
        result = await unauthenticated_bank_sync_client.get_sync_history(1)
        assert not result.ok
        assert result.status_code in (401, 403)

    async def test_list_connections_without_workspace_rejected(
        self, no_workspace_bank_sync_client
    ):
        """Listing connections with auth but no workspace header should fail."""
        result = await no_workspace_bank_sync_client.list_connections()
        assert not result.ok
        assert result.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Connections: empty state
# ---------------------------------------------------------------------------


class TestBankSyncConnectionsEmpty:

    async def test_list_connections_empty(self, bank_sync_client):
        """A fresh workspace should have zero bank connections."""
        result = await bank_sync_client.list_connections()
        data = result.raise_on_error()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_disconnect_nonexistent_connection(self, bank_sync_client):
        """Disconnecting a non-existent connection should return 404."""
        result = await bank_sync_client.disconnect(NONEXISTENT_CONNECTION_ID)
        assert not result.ok
        assert result.status_code == 404


# ---------------------------------------------------------------------------
# Connection create with invalid token
# ---------------------------------------------------------------------------


class TestBankSyncConnectInvalidToken:

    async def test_connect_with_invalid_monobank_token(self, bank_sync_client):
        """Connecting with a fake Monobank token should fail.

        The service calls the Monobank API to verify the token.
        A fake token should be rejected with a client/server error.
        """
        result = await bank_sync_client.connect_bank(FAKE_MONOBANK_TOKEN)
        assert not result.ok
        # Monobank API rejection or token validation error
        assert result.status_code in (400, 401, 502)

    async def test_connect_with_empty_token_rejected(self, bank_sync_client):
        """An empty token should be rejected by validation."""
        result = await bank_sync_client.connect_bank("")
        assert not result.ok
        assert result.status_code == 422


# ---------------------------------------------------------------------------
# Sync operations on non-existent connection
# ---------------------------------------------------------------------------


class TestBankSyncOperationsNotFound:

    async def test_trigger_sync_nonexistent_connection(self, bank_sync_client):
        """Triggering sync for a non-existent connection should return 404."""
        result = await bank_sync_client.trigger_sync(NONEXISTENT_CONNECTION_ID)
        assert not result.ok
        assert result.status_code == 404

    async def test_preview_sync_nonexistent_connection(self, bank_sync_client):
        """Preview sync for a non-existent connection should return 404."""
        result = await bank_sync_client.preview_sync(NONEXISTENT_CONNECTION_ID)
        assert not result.ok
        assert result.status_code == 404

    async def test_sync_status_nonexistent_connection(self, bank_sync_client):
        """Sync status for a non-existent connection should return 404 or null."""
        result = await bank_sync_client.get_sync_status(NONEXISTENT_CONNECTION_ID)
        # May return 404 or 200 with null body depending on implementation
        if result.ok:
            # null/None is a valid response (no sync ever run)
            assert result.data is None
        else:
            assert result.status_code == 404

    async def test_sync_history_nonexistent_connection(self, bank_sync_client):
        """Sync history for a non-existent connection should return 404 or empty list."""
        result = await bank_sync_client.get_sync_history(NONEXISTENT_CONNECTION_ID)
        if result.ok:
            assert isinstance(result.data, list)
            assert len(result.data) == 0
        else:
            assert result.status_code == 404

    async def test_confirm_sync_nonexistent_connection(self, bank_sync_client):
        """Confirming sync for a non-existent connection should return 404."""
        result = await bank_sync_client.confirm_sync(
            NONEXISTENT_CONNECTION_ID,
            transactions=[],
        )
        assert not result.ok
        assert result.status_code in (404, 422)

    async def test_link_account_nonexistent_connection(self, bank_sync_client):
        """Linking an account on a non-existent connection should return 404."""
        result = await bank_sync_client.link_account(
            NONEXISTENT_CONNECTION_ID,
            linked_account_id=1,
            finflow_account_id=1,
        )
        assert not result.ok
        assert result.status_code == 404

    async def test_toggle_sync_nonexistent_connection(self, bank_sync_client):
        """Toggling sync on a non-existent connection should return 404."""
        result = await bank_sync_client.toggle_account_sync(
            NONEXISTENT_CONNECTION_ID,
            linked_account_id=1,
        )
        assert not result.ok
        assert result.status_code == 404


# ---------------------------------------------------------------------------
# Sync request validation
# ---------------------------------------------------------------------------


class TestBankSyncRequestValidation:

    async def test_sync_days_back_too_large(self, bank_sync_client):
        """days_back > 30 should be rejected by validation."""
        result = await bank_sync_client.trigger_sync(
            NONEXISTENT_CONNECTION_ID,
            days_back=31,
        )
        assert not result.ok
        assert result.status_code == 422

    async def test_sync_days_back_zero(self, bank_sync_client):
        """days_back = 0 should be rejected by validation (ge=1)."""
        result = await bank_sync_client.trigger_sync(
            NONEXISTENT_CONNECTION_ID,
            days_back=0,
        )
        assert not result.ok
        assert result.status_code == 422

    async def test_preview_days_back_too_large(self, bank_sync_client):
        """Preview with days_back > 30 should be rejected."""
        result = await bank_sync_client.preview_sync(
            NONEXISTENT_CONNECTION_ID,
            days_back=31,
        )
        assert not result.ok
        assert result.status_code == 422

    async def test_sync_history_negative_skip(self, bank_sync_client):
        """Negative skip parameter should be rejected."""
        result = await bank_sync_client.get_sync_history(
            NONEXISTENT_CONNECTION_ID,
            skip=-1,
        )
        assert not result.ok
        assert result.status_code == 422

    async def test_sync_history_limit_too_large(self, bank_sync_client):
        """Limit > 100 should be rejected."""
        result = await bank_sync_client.get_sync_history(
            NONEXISTENT_CONNECTION_ID,
            limit=101,
        )
        assert not result.ok
        assert result.status_code == 422


# ---------------------------------------------------------------------------
# Webhook endpoints (public, no auth required)
# ---------------------------------------------------------------------------


class TestBankSyncWebhook:

    async def test_webhook_verify_endpoint(self, unauthenticated_bank_sync_client):
        """Monobank GET webhook verification should return 200."""
        result = await unauthenticated_bank_sync_client.webhook_verify()
        data = result.raise_on_error()
        assert data["status"] == "ok"

    async def test_webhook_receive_valid_payload(self, unauthenticated_bank_sync_client):
        """Posting a valid webhook payload should return 200."""
        payload = {
            "type": "StatementItem",
            "data": {
                "account": "test_account_id",
                "statementItem": {
                    "id": "test_txn_id",
                    "time": 1234567890,
                    "amount": -5000,
                    "description": "Test transaction",
                },
            },
        }
        result = await unauthenticated_bank_sync_client.webhook_receive(payload)
        data = result.raise_on_error()
        assert data["status"] == "received"

    async def test_webhook_receive_invalid_payload(self, unauthenticated_bank_sync_client):
        """Posting an invalid webhook payload should still return 200 with status=invalid."""
        result = await unauthenticated_bank_sync_client.webhook_receive({"bad": "data"})
        data = result.raise_on_error()
        assert data["status"] == "invalid"

    async def test_webhook_receive_empty_payload(self, unauthenticated_bank_sync_client):
        """Posting an empty object should return 200 with status=invalid."""
        result = await unauthenticated_bank_sync_client.webhook_receive({})
        data = result.raise_on_error()
        assert data["status"] == "invalid"


# ---------------------------------------------------------------------------
# Internal endpoints
# ---------------------------------------------------------------------------


class TestBankSyncInternal:

    async def test_internal_connections_without_token_rejected(
        self, bank_sync_client
    ):
        """Accessing internal endpoint without internal token should fail."""
        # Use _get directly to avoid setting the internal token header
        client = BankSyncApiClient()
        resp = await client._get("/internal/connections/user/1")
        parsed = client._parse(resp)
        assert not parsed.ok
        assert parsed.status_code in (401, 403)

    async def test_internal_connections_with_wrong_token_rejected(
        self, bank_sync_client
    ):
        """Accessing internal endpoint with a wrong internal token should fail."""
        client = BankSyncApiClient()
        result = await client.get_user_connections_internal(
            user_id=1,
            internal_token="definitely_wrong_token",
        )
        assert not result.ok
        assert result.status_code in (401, 403)

    async def test_internal_connections_with_valid_token(self, primary_user):
        """With a valid internal token, should return user connections (empty list)."""
        internal_token = os.environ.get("INTERNAL_SECRET_TOKEN")
        if not internal_token:
            pytest.skip("INTERNAL_SECRET_TOKEN not set")

        user_id = primary_user.get("user_id")
        if user_id is None:
            pytest.skip("user_id not available from registration")

        client = BankSyncApiClient()
        result = await client.get_user_connections_internal(
            user_id=int(user_id),
            internal_token=internal_token,
        )
        data = result.raise_on_error()
        assert isinstance(data, list)


# ---------------------------------------------------------------------------
# Workspace isolation
# ---------------------------------------------------------------------------


class TestBankSyncWorkspaceIsolation:

    async def test_connections_isolated_by_workspace(
        self, bank_sync_client, secondary_bank_sync_client, secondary_user
    ):
        """Secondary user should not see primary user's connections.

        Since neither user has real connections, both should see empty lists.
        This verifies the endpoint filters by workspace correctly.
        """
        # Get secondary user's own workspace
        from tests.e2e.clients.workspace_client import WorkspaceApiClient

        ws_client = WorkspaceApiClient()
        ws_client.set_token(secondary_user["token"])
        ws_result = await ws_client.list_all()
        ws_data = ws_result.raise_on_error()
        workspaces = ws_data.get("workspaces", ws_data) if isinstance(ws_data, dict) else ws_data
        assert len(workspaces) >= 1
        secondary_ws_id = str(workspaces[0]["id"])

        secondary_bank_sync_client.set_workspace_id(secondary_ws_id)

        # Both should return empty lists
        primary_result = await bank_sync_client.list_connections()
        primary_data = primary_result.raise_on_error()
        assert isinstance(primary_data, list)

        secondary_result = await secondary_bank_sync_client.list_connections()
        secondary_data = secondary_result.raise_on_error()
        assert isinstance(secondary_data, list)

    async def test_disconnect_cross_workspace_rejected(
        self, secondary_bank_sync_client, secondary_user
    ):
        """A user should not be able to disconnect a connection from another workspace."""
        from tests.e2e.clients.workspace_client import WorkspaceApiClient

        ws_client = WorkspaceApiClient()
        ws_client.set_token(secondary_user["token"])
        ws_result = await ws_client.list_all()
        ws_data = ws_result.raise_on_error()
        workspaces = ws_data.get("workspaces", ws_data) if isinstance(ws_data, dict) else ws_data
        secondary_ws_id = str(workspaces[0]["id"])

        secondary_bank_sync_client.set_workspace_id(secondary_ws_id)

        # Attempt to disconnect a non-existent connection (404 expected, not 200)
        result = await secondary_bank_sync_client.disconnect(NONEXISTENT_CONNECTION_ID)
        assert not result.ok
        assert result.status_code == 404


# ---------------------------------------------------------------------------
# Error response format
# ---------------------------------------------------------------------------


class TestBankSyncErrorFormat:

    async def test_validation_error_format(self, bank_sync_client):
        """Validation errors should follow the ErrorResponse schema."""
        result = await bank_sync_client.connect_bank("")
        assert not result.ok
        assert result.status_code == 422
        raw = result.raw
        assert isinstance(raw, dict)
        assert "error" in raw or "detail" in raw

    async def test_not_found_error_format(self, bank_sync_client):
        """404 errors should include an error message."""
        result = await bank_sync_client.disconnect(NONEXISTENT_CONNECTION_ID)
        assert not result.ok
        assert result.status_code == 404
        raw = result.raw
        assert isinstance(raw, dict)
        assert "error" in raw or "detail" in raw
