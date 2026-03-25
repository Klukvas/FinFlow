"""
Tests for service clients: SubscriptionClient and CategoryServiceClient.

Covers:
- SubscriptionClient: feature fetching, upload/record limit checks, limit retrieval
- CategoryServiceClient: MCC category lookup, existence checks, batch operations
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.clients.subscription_client import SubscriptionClient
from app.clients.category_client import CategoryServiceClient


# =========================================================================
# Helpers
# =========================================================================

def _make_response(status_code, json_body=None):
    resp = MagicMock()
    resp.status_code = status_code
    if json_body is not None:
        resp.json.return_value = json_body
    return resp


# =========================================================================
# SubscriptionClient
# =========================================================================

class TestSubscriptionClient:

    @pytest.fixture
    def client(self):
        with patch("app.clients.subscription_client.httpx.Client") as mock_cls:
            mock_http = MagicMock()
            mock_cls.return_value = mock_http
            c = SubscriptionClient(base_url="http://test-subscription")
            yield c

    def test_get_user_features_success(self, client):
        features_list = [
            {"feature_code": "pdf_uploads_per_month", "enabled": True, "limit_value": 10},
            {"feature_code": "pdf_records_per_upload", "enabled": True, "limit_value": 100},
        ]
        client.client.get.return_value = _make_response(200, features_list)

        result = client.get_user_features(42)

        assert "pdf_uploads_per_month" in result
        assert result["pdf_uploads_per_month"]["limit_value"] == 10

    def test_get_user_features_non_200_returns_empty(self, client):
        client.client.get.return_value = _make_response(404)

        result = client.get_user_features(42)

        assert result == {}

    def test_get_user_features_exception_returns_empty(self, client):
        client.client.get.side_effect = Exception("Connection refused")

        result = client.get_user_features(42)

        assert result == {}

    def test_check_pdf_upload_limit_allowed(self, client):
        client.get_user_features = MagicMock(return_value={
            "pdf_uploads_per_month": {"enabled": True, "limit_value": 10}
        })

        assert client.check_pdf_upload_limit(42, 5) is True

    def test_check_pdf_upload_limit_at_limit(self, client):
        client.get_user_features = MagicMock(return_value={
            "pdf_uploads_per_month": {"enabled": True, "limit_value": 5}
        })

        assert client.check_pdf_upload_limit(42, 5) is False

    def test_check_pdf_upload_limit_exceeded(self, client):
        client.get_user_features = MagicMock(return_value={
            "pdf_uploads_per_month": {"enabled": True, "limit_value": 3}
        })

        assert client.check_pdf_upload_limit(42, 5) is False

    def test_check_pdf_upload_limit_unlimited(self, client):
        client.get_user_features = MagicMock(return_value={
            "pdf_uploads_per_month": {"enabled": True, "limit_value": None}
        })

        assert client.check_pdf_upload_limit(42, 999) is True

    def test_check_pdf_upload_limit_feature_disabled(self, client):
        client.get_user_features = MagicMock(return_value={
            "pdf_uploads_per_month": {"enabled": False, "limit_value": 100}
        })

        assert client.check_pdf_upload_limit(42, 0) is False

    def test_check_pdf_upload_limit_no_feature(self, client):
        client.get_user_features = MagicMock(return_value={})

        assert client.check_pdf_upload_limit(42, 0) is False

    def test_check_pdf_records_limit_allowed(self, client):
        client.get_user_features = MagicMock(return_value={
            "pdf_records_per_upload": {"enabled": True, "limit_value": 100}
        })

        assert client.check_pdf_records_limit(42, 50) is True

    def test_check_pdf_records_limit_at_limit(self, client):
        """At-limit should be allowed (<=)."""
        client.get_user_features = MagicMock(return_value={
            "pdf_records_per_upload": {"enabled": True, "limit_value": 50}
        })

        assert client.check_pdf_records_limit(42, 50) is True

    def test_check_pdf_records_limit_exceeded(self, client):
        client.get_user_features = MagicMock(return_value={
            "pdf_records_per_upload": {"enabled": True, "limit_value": 20}
        })

        assert client.check_pdf_records_limit(42, 25) is False

    def test_check_pdf_records_limit_unlimited(self, client):
        client.get_user_features = MagicMock(return_value={
            "pdf_records_per_upload": {"enabled": True, "limit_value": None}
        })

        assert client.check_pdf_records_limit(42, 999) is True

    def test_check_pdf_records_limit_feature_disabled(self, client):
        client.get_user_features = MagicMock(return_value={
            "pdf_records_per_upload": {"enabled": False, "limit_value": 100}
        })

        assert client.check_pdf_records_limit(42, 5) is False

    def test_get_pdf_limits(self, client):
        client.get_user_features = MagicMock(return_value={
            "pdf_uploads_per_month": {"limit_value": 10, "plan_code": "professional"},
            "pdf_records_per_upload": {"limit_value": 100},
        })

        limits = client.get_pdf_limits(42)

        assert limits["uploads_per_month"] == 10
        assert limits["records_per_upload"] == 100
        assert limits["plan_code"] == "professional"

    def test_get_pdf_limits_empty_features(self, client):
        client.get_user_features = MagicMock(return_value={})

        limits = client.get_pdf_limits(42)

        assert limits["uploads_per_month"] is None
        assert limits["records_per_upload"] is None
        assert limits["plan_code"] == "unknown"

    def test_close(self, client):
        client.close()
        client.client.close.assert_called_once()


# =========================================================================
# CategoryServiceClient
# =========================================================================

class TestCategoryServiceClient:

    @pytest.fixture
    def client(self):
        c = CategoryServiceClient()
        mock_http = AsyncMock()
        mock_http.is_closed = False
        c._client = mock_http
        return c

    @pytest.mark.asyncio
    async def test_get_mcc_category_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "items": [
                {"mcc_code": 5411, "name": "Grocery", "translation": "Продукты", "is_default": True},
                {"mcc_code": 5812, "name": "Restaurants", "translation": "Рестораны", "is_default": True},
            ]
        }
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.get_mcc_category(5411, "ru")

        assert result is not None
        assert result["mcc_code"] == 5411
        assert result["name"] == "Grocery"

    @pytest.mark.asyncio
    async def test_get_mcc_category_not_found(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"items": []}
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.get_mcc_category(9999, "en")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_mcc_category_api_error(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.get_mcc_category(5411, "en")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_mcc_category_exception(self, client):
        client._client.get = AsyncMock(side_effect=Exception("Network error"))

        result = await client.get_mcc_category(5411, "en")

        assert result is None

    @pytest.mark.asyncio
    async def test_check_category_exists_true(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"exists": True}
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.check_category_exists(5411, 42)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_category_exists_false(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"exists": False}
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.check_category_exists(5411, 42)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_category_exists_api_error(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.check_category_exists(5411, 42)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_category_exists_exception(self, client):
        client._client.get = AsyncMock(side_effect=Exception("Timeout"))

        result = await client.check_category_exists(5411, 42)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_category_by_mcc_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"exists": True, "category_id": 42}
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.get_category_by_mcc(5411, 1)

        assert result["exists"] is True
        assert result["category_id"] == 42

    @pytest.mark.asyncio
    async def test_get_category_by_mcc_not_found(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.get_category_by_mcc(5411, 1)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_category_by_mcc_exception(self, client):
        client._client.get = AsyncMock(side_effect=Exception("Error"))

        result = await client.get_category_by_mcc(5411, 1)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_default_categories_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"categories": [{"id": 1, "name": "Food"}]}
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.get_default_categories("en")

        assert result is not None
        assert "categories" in result

    @pytest.mark.asyncio
    async def test_get_default_categories_error(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        client._client.get = AsyncMock(return_value=mock_resp)

        result = await client.get_default_categories("en")

        assert result is None

    @pytest.mark.asyncio
    async def test_check_categories_batch_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"mcc_code": 5411, "exists": True, "category_id": 1},
                {"mcc_code": 5812, "exists": False, "category_id": None},
            ]
        }
        client._client.post = AsyncMock(return_value=mock_resp)

        result = await client.check_categories_exist_by_mcc_batch([5411, 5812], 42)

        assert result is not None
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_check_categories_batch_error(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        client._client.post = AsyncMock(return_value=mock_resp)

        result = await client.check_categories_exist_by_mcc_batch([5411], 42)

        assert result is None

    @pytest.mark.asyncio
    async def test_check_categories_batch_exception(self, client):
        client._client.post = AsyncMock(side_effect=Exception("Network"))

        result = await client.check_categories_exist_by_mcc_batch([5411], 42)

        assert result is None

    @pytest.mark.asyncio
    async def test_close_client(self, client):
        mock_http = client._client
        await client.close()
        mock_http.aclose.assert_awaited_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_when_already_closed(self):
        c = CategoryServiceClient()
        c._client = None
        # Should not raise
        await c.close()
