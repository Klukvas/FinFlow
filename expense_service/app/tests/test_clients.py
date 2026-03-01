"""
Tests for client modules: account_service_client, category_service_client,
currency_service_client, subscription, workspace.
Uses unittest.mock to patch httpx HTTP calls.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import UUID
from fastapi import HTTPException

from app.clients.account_service_client import AccountServiceClient
from app.clients.category_service_client import CategoryServiceClient
from shared.clients.currency_service import CurrencyServiceClient
from shared.clients import SubscriptionClient
from shared.clients import WorkspaceClient
from shared.clients.base import ExternalServiceError

# Capture the REAL (unpatched) method references before any autouse conftest
# mock has a chance to replace them at the class level.
_REAL_CHECK_LIMIT = SubscriptionClient.check_limit
_REAL_WORKSPACE_AUTHORIZE = WorkspaceClient.authorize

WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
USER_ID = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(status_code: int, json_body=None, text_body=""):
    resp = MagicMock()
    resp.status_code = status_code
    if json_body is not None:
        resp.json.return_value = json_body
    resp.text = text_body
    return resp


# ---------------------------------------------------------------------------
# AccountServiceClient tests
# ---------------------------------------------------------------------------

class TestAccountServiceClient:
    @pytest.fixture
    def client(self):
        """Return AccountServiceClient with the underlying httpx client mocked."""
        with patch("shared.clients.base.httpx.Client") as mock_httpx:
            c = AccountServiceClient()
            c.client = MagicMock()
            yield c

    def test_validate_account_success(self, client):
        client.client.request.return_value = _make_response(200, {"account": {"id": 5, "currency": "USD"}})
        result = client.validate_account(5, USER_ID)
        assert result["account"]["id"] == 5

    def test_validate_account_404_raises_http_400(self, client):
        client.client.request.return_value = _make_response(404)
        with pytest.raises(HTTPException) as exc_info:
            client.validate_account(5, USER_ID)
        assert exc_info.value.status_code == 400
        assert "not found" in exc_info.value.detail.lower()

    def test_validate_account_403_raises_http_400(self, client):
        client.client.request.return_value = _make_response(403)
        with pytest.raises(HTTPException) as exc_info:
            client.validate_account(5, USER_ID)
        assert exc_info.value.status_code == 400
        assert "not owned" in exc_info.value.detail.lower()

    def test_validate_account_500_raises_http_500(self, client):
        client.client.request.return_value = _make_response(500)
        with pytest.raises(HTTPException) as exc_info:
            client.validate_account(5, USER_ID)
        assert exc_info.value.status_code == 500

    def test_validate_account_request_error_raises_external_service(self, client):
        import httpx
        client.client.request.side_effect = httpx.RequestError("connection refused")
        with pytest.raises(ExternalServiceError):
            client.validate_account(5, USER_ID)

    def test_update_account_balance_success(self, client):
        client.client.request.return_value = _make_response(200, {"account": {"id": 5, "balance": 900.0}})
        result = client.update_account_balance(5, USER_ID, -100.0, "USD")
        assert result["account"]["balance"] == 900.0

    def test_update_account_balance_404_raises_http_400(self, client):
        client.client.request.return_value = _make_response(404)
        with pytest.raises(HTTPException) as exc_info:
            client.update_account_balance(5, USER_ID, -100.0)
        assert exc_info.value.status_code == 400

    def test_update_account_balance_400_raises_http_400(self, client):
        client.client.request.return_value = _make_response(400)
        with pytest.raises(HTTPException) as exc_info:
            client.update_account_balance(5, USER_ID, -10000.0)
        assert exc_info.value.status_code == 400
        assert "insufficient" in exc_info.value.detail.lower()

    def test_update_account_balance_unexpected_status_raises_500(self, client):
        client.client.request.return_value = _make_response(503)
        with pytest.raises(HTTPException) as exc_info:
            client.update_account_balance(5, USER_ID, -100.0)
        assert exc_info.value.status_code == 500

    def test_update_account_balance_request_error_raises_external(self, client):
        import httpx
        client.client.request.side_effect = httpx.RequestError("timeout")
        with pytest.raises(ExternalServiceError):
            client.update_account_balance(5, USER_ID, -100.0)


# ---------------------------------------------------------------------------
# CategoryServiceClient tests
# ---------------------------------------------------------------------------

class TestCategoryServiceClient:
    @pytest.fixture
    def client(self):
        with patch("shared.clients.base.httpx.Client"):
            c = CategoryServiceClient()
            c.client = MagicMock()
            yield c

    def test_validate_category_none_returns_empty_dict(self, client):
        result = client.validate_category(None, USER_ID, WORKSPACE_ID)
        assert result == {}

    def test_validate_category_no_workspace_raises_400(self, client):
        with pytest.raises(HTTPException) as exc_info:
            client.validate_category(1, USER_ID, None)
        assert exc_info.value.status_code == 400

    def test_validate_category_success(self, client):
        client.client.request.return_value = _make_response(200, {"id": 1, "name": "Food"})
        result = client.validate_category(1, USER_ID, WORKSPACE_ID)
        assert result["id"] == 1

    def test_validate_category_404_raises_http_400(self, client):
        client.client.request.return_value = _make_response(404)
        with pytest.raises(HTTPException) as exc_info:
            client.validate_category(1, USER_ID, WORKSPACE_ID)
        assert exc_info.value.status_code == 400

    def test_validate_category_403_raises_http_400(self, client):
        client.client.request.return_value = _make_response(403)
        with pytest.raises(HTTPException) as exc_info:
            client.validate_category(1, USER_ID, WORKSPACE_ID)
        assert exc_info.value.status_code == 400

    def test_validate_category_unexpected_status_raises_500(self, client):
        client.client.request.return_value = _make_response(503)
        with pytest.raises(HTTPException) as exc_info:
            client.validate_category(1, USER_ID, WORKSPACE_ID)
        assert exc_info.value.status_code == 500

    def test_validate_category_request_error_raises_external(self, client):
        import httpx
        client.client.request.side_effect = httpx.RequestError("refused")
        with pytest.raises(ExternalServiceError):
            client.validate_category(1, USER_ID, WORKSPACE_ID)


# ---------------------------------------------------------------------------
# CurrencyServiceClient tests
# ---------------------------------------------------------------------------

class TestCurrencyServiceClient:
    @pytest.fixture
    def client(self):
        with patch("shared.clients.currency_service.httpx.Client") as mock_cls:
            mock_http = MagicMock()
            mock_cls.return_value = mock_http
            c = CurrencyServiceClient(base_url="http://currency-svc")
            yield c

    def test_convert_amount_success(self, client):
        client.client.post.return_value = _make_response(200, {"converted_amount": 90.0, "rate": 0.9})
        result = client.convert_amount(100.0, "USD", "EUR")
        assert result == 90.0

    def test_convert_amount_non_200_returns_none(self, client):
        client.client.post.return_value = _make_response(400, text_body="error")
        result = client.convert_amount(100.0, "USD", "EUR")
        assert result is None

    def test_convert_amount_exception_returns_none(self, client):
        client.client.post.side_effect = Exception("network error")
        result = client.convert_amount(100.0, "USD", "EUR")
        assert result is None

    def test_get_exchange_rate_success(self, client):
        client.client.post.return_value = _make_response(200, {"rate": 0.85, "converted_amount": 0.85})
        rate = client.get_exchange_rate("USD", "EUR")
        assert rate == 0.85

    def test_get_exchange_rate_non_200_returns_none(self, client):
        client.client.post.return_value = _make_response(500)
        rate = client.get_exchange_rate("USD", "EUR")
        assert rate is None

    def test_get_exchange_rate_exception_returns_none(self, client):
        client.client.post.side_effect = Exception("timeout")
        rate = client.get_exchange_rate("USD", "EUR")
        assert rate is None

    def test_same_currency_no_conversion_needed(self, client):
        client.client.post.return_value = _make_response(200, {"converted_amount": 100.0, "rate": 1.0})
        result = client.convert_amount(100.0, "USD", "USD")
        assert result == 100.0


# ---------------------------------------------------------------------------
# SubscriptionClient tests
# NOTE: conftest.py has an autouse mock that patches
# `shared.clients.subscription.SubscriptionClient.check_limit` at the class
# level, returning True for ALL tests. To test the real logic we must call the
# original unpatched function directly using the class __dict__ descriptor.
# ---------------------------------------------------------------------------

def _call_real_check_limit(instance, user_id, current_count, feature_code="expenses"):
    """Call the original check_limit bypassing the autouse class-level mock."""
    original_fn = SubscriptionClient.__dict__.get("check_limit")
    if original_fn is None:
        raise RuntimeError("Could not find original check_limit in __dict__")
    return original_fn(instance, user_id, current_count, feature_code)


class TestSubscriptionClient:
    @pytest.fixture
    def sub_client(self):
        """Return a SubscriptionClient with HTTP layer mocked."""
        with patch("shared.clients.subscription.httpx.Client") as mock_cls:
            mock_http = MagicMock()
            mock_cls.return_value = mock_http
            c = SubscriptionClient(base_url="http://subscription-svc")
            yield c

    def test_get_user_features_success(self, sub_client):
        features_list = [
            {"feature_code": "expenses", "enabled": True, "limit_value": 100}
        ]
        sub_client.client.get.return_value = _make_response(200, features_list)
        result = sub_client.get_user_features(USER_ID)
        assert "expenses" in result
        assert result["expenses"]["enabled"] is True

    def test_get_user_features_non_200_returns_empty(self, sub_client):
        sub_client.client.get.return_value = _make_response(404)
        result = sub_client.get_user_features(USER_ID)
        assert result == {}

    def test_get_user_features_exception_returns_empty(self, sub_client):
        sub_client.client.get.side_effect = Exception("timeout")
        result = sub_client.get_user_features(USER_ID)
        assert result is None or result == {}

    # Tests for check_limit (formerly check_expense_limit)
    def test_check_limit_feature_disabled_returns_false(self, sub_client):
        sub_client.get_user_features = MagicMock(return_value={
            "expenses": {"enabled": False, "limit_value": 100}
        })
        result = _REAL_CHECK_LIMIT(sub_client, USER_ID, 5, "expenses")
        assert result is False

    def test_check_limit_unlimited_returns_true(self, sub_client):
        sub_client.get_user_features = MagicMock(return_value={
            "expenses": {"enabled": True, "limit_value": None}
        })
        result = _REAL_CHECK_LIMIT(sub_client, USER_ID, 999, "expenses")
        assert result is True

    def test_check_limit_under_limit_returns_true(self, sub_client):
        sub_client.get_user_features = MagicMock(return_value={
            "expenses": {"enabled": True, "limit_value": 50}
        })
        result = _REAL_CHECK_LIMIT(sub_client, USER_ID, 49, "expenses")
        assert result is True

    def test_check_limit_at_limit_returns_false(self, sub_client):
        sub_client.get_user_features = MagicMock(return_value={
            "expenses": {"enabled": True, "limit_value": 50}
        })
        result = _REAL_CHECK_LIMIT(sub_client, USER_ID, 50, "expenses")
        assert result is False

    def test_check_limit_no_expense_feature_returns_false(self, sub_client):
        sub_client.get_user_features = MagicMock(return_value={})
        result = _REAL_CHECK_LIMIT(sub_client, USER_ID, 0, "expenses")
        assert result is False


# ---------------------------------------------------------------------------
# WorkspaceClient tests
# NOTE: The conftest.py autouse fixture patches WorkspaceClient.authorize at
# the class level (via patch). To test the real authorize() implementation,
# we use a fresh WorkspaceClient and call the UNPATCHED method by accessing
# it via the class (bypassing the instance-level mock).
# Since the autouse patch uses `patch("shared.clients.workspace.WorkspaceClient.authorize")`
# (not the workspace module itself), our direct calls to WorkspaceClient().authorize()
# from shared.clients.workspace are affected. We need to call the underlying
# implementation directly via `WorkspaceClient.authorize.__wrapped__` or
# test through the real module path before the mock is applied.
#
# Simpler approach: instantiate WorkspaceClient and call real methods, but
# use patch.object to restore the original method for the duration of the test.
# ---------------------------------------------------------------------------

class TestWorkspaceClient:
    @pytest.fixture
    def real_client(self):
        """WorkspaceClient with the autouse mock temporarily removed."""
        # The autouse mock is on shared.clients.workspace.WorkspaceClient.authorize
        # We need to access the original (unpatched) WorkspaceClient from shared.clients.workspace
        from shared.clients.workspace import WorkspaceClient as _WC
        return _WC()

    def test_get_headers_includes_token(self, real_client):
        headers = real_client._get_headers()
        assert "X-Internal-Token" in headers
        assert "Content-Type" in headers

    def test_get_headers_without_token(self):
        from shared.clients.workspace import WorkspaceClient as _WC
        c = _WC()
        c.internal_token = None
        headers = c._get_headers()
        # Token header should not be present when token is None
        assert "X-Internal-Token" not in headers

    def _authorize_real(self, client, status_code, json_body=None, side_effect=None):
        """Call the REAL (unpatched) authorize() with a mocked HTTP response."""
        mock_resp = _make_response(status_code, json_body)
        mock_post = MagicMock()
        if side_effect:
            mock_post.side_effect = side_effect
        else:
            mock_post.return_value = mock_resp
        client.client = MagicMock()
        client.client.post = mock_post
        return _REAL_WORKSPACE_AUTHORIZE(client, WORKSPACE_ID, USER_ID, "member")

    def test_authorize_success_200(self, real_client):
        authorized, role = self._authorize_real(
            real_client, 200, {"authorized": True, "role": "owner"}
        )
        assert authorized is True
        assert role == "owner"

    def test_authorize_200_unauthorized_false(self, real_client):
        authorized, role = self._authorize_real(
            real_client, 200, {"authorized": False, "role": None}
        )
        assert authorized is False

    def test_authorize_403_returns_false(self, real_client):
        authorized, role = self._authorize_real(real_client, 403)
        assert authorized is False
        assert role is None

    def test_authorize_404_returns_false(self, real_client):
        authorized, role = self._authorize_real(real_client, 404)
        assert authorized is False

    def test_authorize_unexpected_status_returns_false(self, real_client):
        authorized, role = self._authorize_real(real_client, 500)
        assert authorized is False

    def test_authorize_timeout_returns_false(self, real_client):
        import httpx
        authorized, role = self._authorize_real(
            real_client, 200, side_effect=httpx.TimeoutException("timeout")
        )
        assert authorized is False

    def test_authorize_request_error_returns_false(self, real_client):
        import httpx
        authorized, role = self._authorize_real(
            real_client, 200, side_effect=httpx.RequestError("connection refused")
        )
        assert authorized is False

    def test_authorize_generic_exception_returns_false(self, real_client):
        authorized, role = self._authorize_real(
            real_client, 200, side_effect=RuntimeError("unexpected")
        )
        assert authorized is False

    def _get_role_with_mock_response(self, client, status_code, json_body=None, side_effect=None):
        mock_resp = _make_response(status_code, json_body)
        mock_get = MagicMock()
        if side_effect:
            mock_get.side_effect = side_effect
        else:
            mock_get.return_value = mock_resp
        client.client = MagicMock()
        client.client.get = mock_get
        return client.get_user_role(WORKSPACE_ID, USER_ID)

    def test_get_user_role_success(self, real_client):
        role = self._get_role_with_mock_response(real_client, 200, {"role": "admin"})
        assert role == "admin"

    def test_get_user_role_non_200_returns_none(self, real_client):
        role = self._get_role_with_mock_response(real_client, 404)
        assert role is None

    def test_get_user_role_exception_returns_none(self, real_client):
        role = self._get_role_with_mock_response(
            real_client, 200, side_effect=Exception("network")
        )
        assert role is None
