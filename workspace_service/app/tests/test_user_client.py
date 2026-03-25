"""
Unit tests for the UserClient HTTP client.

Tests cover:
- get_user: success, 404, unexpected status, request error
- get_user_by_email: success, 404, unexpected status, request error
- user_exists: delegates to get_user
- get_users_batch: aggregates get_user calls
"""
import pytest
from unittest.mock import patch, MagicMock

import httpx

from app.clients.user import UserClient, UserInfo


def _user_response(user_id: int = 1, email: str = "user@test.com") -> dict:
    """Return a valid user-service JSON body."""
    return {
        "id": user_id,
        "email": email,
        "base_currency": "USD",
        "default_workspace_id": None,
    }


class TestGetUser:
    """Tests for UserClient.get_user()."""

    @patch("app.clients.user.httpx.Client")
    def test_success(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _user_response()
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.return_value = mock_resp
        mock_client_cls.return_value = ctx

        client = UserClient()
        result = client.get_user(1)

        assert isinstance(result, UserInfo)
        assert result.id == 1
        assert result.email == "user@test.com"
        assert result.base_currency == "USD"

    @patch("app.clients.user.httpx.Client")
    def test_not_found(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.return_value = mock_resp
        mock_client_cls.return_value = ctx

        client = UserClient()
        assert client.get_user(999) is None

    @patch("app.clients.user.httpx.Client")
    def test_unexpected_status(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.return_value = mock_resp
        mock_client_cls.return_value = ctx

        client = UserClient()
        assert client.get_user(1) is None

    @patch("app.clients.user.httpx.Client")
    def test_request_error(self, mock_client_cls):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.side_effect = httpx.RequestError("Connection refused", request=MagicMock())
        mock_client_cls.return_value = ctx

        client = UserClient()
        assert client.get_user(1) is None

    @patch("app.clients.user.httpx.Client")
    def test_default_workspace_id_returned(self, mock_client_cls):
        body = _user_response()
        body["default_workspace_id"] = "ws-123"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = body
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.return_value = mock_resp
        mock_client_cls.return_value = ctx

        client = UserClient()
        result = client.get_user(1)
        assert result.default_workspace_id == "ws-123"


class TestGetUserByEmail:
    """Tests for UserClient.get_user_by_email()."""

    @patch("app.clients.user.httpx.Client")
    def test_success(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _user_response(email="found@test.com")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.return_value = mock_resp
        mock_client_cls.return_value = ctx

        client = UserClient()
        result = client.get_user_by_email("found@test.com")
        assert result is not None
        assert result.email == "found@test.com"

    @patch("app.clients.user.httpx.Client")
    def test_not_found(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.return_value = mock_resp
        mock_client_cls.return_value = ctx

        client = UserClient()
        assert client.get_user_by_email("nobody@test.com") is None

    @patch("app.clients.user.httpx.Client")
    def test_unexpected_status(self, mock_client_cls):
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.return_value = mock_resp
        mock_client_cls.return_value = ctx

        client = UserClient()
        assert client.get_user_by_email("user@test.com") is None

    @patch("app.clients.user.httpx.Client")
    def test_request_error(self, mock_client_cls):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.side_effect = httpx.RequestError("timeout", request=MagicMock())
        mock_client_cls.return_value = ctx

        client = UserClient()
        assert client.get_user_by_email("user@test.com") is None


class TestUserExists:
    """Tests for UserClient.user_exists()."""

    @patch.object(UserClient, "get_user")
    def test_exists(self, mock_get):
        mock_get.return_value = UserInfo(id=1, email="a@b.com", base_currency="USD")
        client = UserClient()
        assert client.user_exists(1) is True

    @patch.object(UserClient, "get_user")
    def test_not_exists(self, mock_get):
        mock_get.return_value = None
        client = UserClient()
        assert client.user_exists(999) is False


class TestGetUsersBatch:
    """Tests for UserClient.get_users_batch()."""

    @patch.object(UserClient, "get_user")
    def test_some_found(self, mock_get):
        user1 = UserInfo(id=1, email="a@b.com", base_currency="USD")
        mock_get.side_effect = lambda uid: user1 if uid == 1 else None

        client = UserClient()
        result = client.get_users_batch([1, 2, 3])
        assert 1 in result
        assert 2 not in result
        assert 3 not in result

    @patch.object(UserClient, "get_user")
    def test_empty_list(self, mock_get):
        client = UserClient()
        result = client.get_users_batch([])
        assert result == {}
        mock_get.assert_not_called()

    @patch.object(UserClient, "get_user")
    def test_all_found(self, mock_get):
        users = {
            1: UserInfo(id=1, email="a@b.com", base_currency="USD"),
            2: UserInfo(id=2, email="c@d.com", base_currency="EUR"),
        }
        mock_get.side_effect = lambda uid: users.get(uid)

        client = UserClient()
        result = client.get_users_batch([1, 2])
        assert len(result) == 2


class TestUserInfo:
    """Tests for UserInfo dataclass."""

    def test_default_workspace_id_none(self):
        info = UserInfo(id=1, email="a@b.com", base_currency="USD")
        assert info.default_workspace_id is None

    def test_with_workspace_id(self):
        info = UserInfo(id=1, email="a@b.com", base_currency="USD", default_workspace_id="ws-1")
        assert info.default_workspace_id == "ws-1"
