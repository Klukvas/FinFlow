"""
Tests for app/clients/currency.py and app/clients/workspace.py
Covers:
  - currency.py: 52% -> target 80%+  (lines 30-38, 47-58)
  - workspace.py: 47% -> target 80%+  (lines 70-93, 108-121, 133-191)
"""
import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID

import httpx

from app.clients.currency import CurrencyClient
from app.clients.workspace import WorkspaceClient


# ---------------------------------------------------------------------------
# CurrencyClient
# ---------------------------------------------------------------------------

class TestCurrencyClientValidateCurrency:
    """Tests for CurrencyClient.validate_currency (lines 13-43)."""

    def test_returns_true_when_currency_is_supported(self):
        """Lines 30-35: returns True when code is in the list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "currencies": [
                {"code": "USD"},
                {"code": "EUR"},
            ]
        }

        with patch.object(CurrencyClient, "__init__", lambda self, *a, **kw: None):
            client = CurrencyClient.__new__(CurrencyClient)
            client.base_url = "http://fake"
            client.client = MagicMock()
            client.client.get.return_value = mock_response

            assert client.validate_currency("USD") is True

    def test_returns_false_when_currency_not_in_list(self):
        """Returns False when currency code is absent from the list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"currencies": [{"code": "USD"}]}

        with patch.object(CurrencyClient, "__init__", lambda self, *a, **kw: None):
            client = CurrencyClient.__new__(CurrencyClient)
            client.base_url = "http://fake"
            client.client = MagicMock()
            client.client.get.return_value = mock_response

            assert client.validate_currency("XYZ") is False

    def test_returns_false_on_non_200_response(self):
        """Lines 37-38: non-200 status returns False."""
        mock_response = MagicMock()
        mock_response.status_code = 503

        with patch.object(CurrencyClient, "__init__", lambda self, *a, **kw: None):
            client = CurrencyClient.__new__(CurrencyClient)
            client.base_url = "http://fake"
            client.client = MagicMock()
            client.client.get.return_value = mock_response

            assert client.validate_currency("USD") is False

    def test_returns_false_on_exception(self):
        """Lines 40-43: any exception results in False."""
        with patch.object(CurrencyClient, "__init__", lambda self, *a, **kw: None):
            client = CurrencyClient.__new__(CurrencyClient)
            client.base_url = "http://fake"
            client.client = MagicMock()
            client.client.get.side_effect = httpx.ConnectError("unreachable")

            assert client.validate_currency("USD") is False


class TestCurrencyClientGetSupportedCurrencies:
    """Tests for CurrencyClient.get_supported_currencies (lines 45-58)."""

    def test_returns_currency_list_on_200(self):
        """Lines 47-54: returns list of currencies."""
        currencies = [{"code": "USD"}, {"code": "EUR"}]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"currencies": currencies}

        with patch.object(CurrencyClient, "__init__", lambda self, *a, **kw: None):
            client = CurrencyClient.__new__(CurrencyClient)
            client.base_url = "http://fake"
            client.client = MagicMock()
            client.client.get.return_value = mock_response

            result = client.get_supported_currencies()
            assert result == currencies

    def test_returns_empty_list_on_non_200(self):
        """Lines 55-56: non-200 returns empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(CurrencyClient, "__init__", lambda self, *a, **kw: None):
            client = CurrencyClient.__new__(CurrencyClient)
            client.base_url = "http://fake"
            client.client = MagicMock()
            client.client.get.return_value = mock_response

            result = client.get_supported_currencies()
            assert result == []

    def test_returns_empty_list_on_exception(self):
        """Lines 57-58: exception returns empty list."""
        with patch.object(CurrencyClient, "__init__", lambda self, *a, **kw: None):
            client = CurrencyClient.__new__(CurrencyClient)
            client.base_url = "http://fake"
            client.client = MagicMock()
            client.client.get.side_effect = Exception("network error")

            result = client.get_supported_currencies()
            assert result == []


# ---------------------------------------------------------------------------
# WorkspaceClient
# ---------------------------------------------------------------------------

class TestWorkspaceClientCreatePersonalWorkspace:
    """Tests for WorkspaceClient.create_personal_workspace (lines 36-121)."""

    def _make_client(self):
        """Return a WorkspaceClient with mocked httpx."""
        with patch.object(WorkspaceClient, "__init__", lambda self: None):
            client = WorkspaceClient.__new__(WorkspaceClient)
            client.base_url = "http://fake-workspace"
            client.internal_token = "test-token"
            client.timeout = 5.0
            return client

    def test_returns_uuid_on_201(self):
        """Lines 70-82: successful 201 returns UUID."""
        ws_client = self._make_client()
        ws_id = "12345678-1234-5678-1234-567812345678"
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"workspace_id": ws_id}

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = mock_resp

        with patch("httpx.Client", return_value=mock_http):
            result = ws_client.create_personal_workspace(user_id=1, max_retries=1, retry_delay=0)

        assert result == UUID(ws_id)

    def test_returns_none_on_non_201(self):
        """Lines 83-93: non-201 response returns None."""
        ws_client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "internal error"

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.return_value = mock_resp

        with patch("httpx.Client", return_value=mock_http):
            result = ws_client.create_personal_workspace(user_id=1, max_retries=1, retry_delay=0)

        assert result is None

    def test_retries_on_connect_error_then_returns_none(self):
        """Lines 95-107: ConnectError triggers retry and eventually returns None."""
        ws_client = self._make_client()

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.side_effect = httpx.ConnectError("refused")

        with patch("httpx.Client", return_value=mock_http), \
             patch("time.sleep"):  # Speed up test
            result = ws_client.create_personal_workspace(user_id=1, max_retries=2, retry_delay=0)

        assert result is None

    def test_request_error_returns_none(self):
        """Lines 108-113: RequestError (not ConnectError) returns None immediately."""
        ws_client = self._make_client()

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        # httpx.RequestError is a base class; use a concrete subclass
        mock_http.post.side_effect = httpx.ReadError("read error")

        with patch("httpx.Client", return_value=mock_http):
            result = ws_client.create_personal_workspace(user_id=1, max_retries=1, retry_delay=0)

        assert result is None

    def test_unexpected_exception_returns_none(self):
        """Lines 114-119: unexpected exception returns None."""
        ws_client = self._make_client()

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.post.side_effect = RuntimeError("unexpected")

        with patch("httpx.Client", return_value=mock_http):
            result = ws_client.create_personal_workspace(user_id=1, max_retries=1, retry_delay=0)

        assert result is None


class TestWorkspaceClientGetDefaultWorkspace:
    """Tests for WorkspaceClient.get_user_default_workspace (lines 123-191)."""

    def _make_client(self):
        with patch.object(WorkspaceClient, "__init__", lambda self: None):
            client = WorkspaceClient.__new__(WorkspaceClient)
            client.base_url = "http://fake-workspace"
            client.internal_token = "test-token"
            client.timeout = 5.0
            return client

    def test_returns_uuid_on_200(self):
        """Lines 142-153: 200 response returns UUID."""
        ws_client = self._make_client()
        ws_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"workspace_id": ws_id}

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.get.return_value = mock_resp

        with patch("httpx.Client", return_value=mock_http):
            result = ws_client.get_user_default_workspace(user_id=1)

        assert result == UUID(ws_id)

    def test_returns_none_on_404(self):
        """Lines 154-162: 404 returns None."""
        ws_client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.get.return_value = mock_resp

        with patch("httpx.Client", return_value=mock_http):
            result = ws_client.get_user_default_workspace(user_id=1)

        assert result is None

    def test_returns_none_on_other_status(self):
        """Lines 163-172: non-200/404 status returns None."""
        ws_client = self._make_client()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "error"

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.get.return_value = mock_resp

        with patch("httpx.Client", return_value=mock_http):
            result = ws_client.get_user_default_workspace(user_id=1)

        assert result is None

    def test_returns_none_on_timeout(self):
        """Lines 174-178: TimeoutException returns None."""
        ws_client = self._make_client()

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.get.side_effect = httpx.TimeoutException("timed out")

        with patch("httpx.Client", return_value=mock_http):
            result = ws_client.get_user_default_workspace(user_id=1)

        assert result is None

    def test_returns_none_on_request_error(self):
        """Lines 180-185: RequestError returns None."""
        ws_client = self._make_client()

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.get.side_effect = httpx.ReadError("read error")

        with patch("httpx.Client", return_value=mock_http):
            result = ws_client.get_user_default_workspace(user_id=1)

        assert result is None

    def test_returns_none_on_unexpected_exception(self):
        """Lines 186-191: unexpected exception returns None."""
        ws_client = self._make_client()

        mock_http = MagicMock()
        mock_http.__enter__ = MagicMock(return_value=mock_http)
        mock_http.__exit__ = MagicMock(return_value=False)
        mock_http.get.side_effect = RuntimeError("something weird")

        with patch("httpx.Client", return_value=mock_http):
            result = ws_client.get_user_default_workspace(user_id=1)

        assert result is None
