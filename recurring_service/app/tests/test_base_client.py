"""Tests for BaseServiceClient.post() params support"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.clients.base import BaseServiceClient


class TestBaseServiceClientPost:
    @pytest.mark.asyncio
    async def test_post_forwards_params_to_make_request(self):
        """Verify post() passes params to _make_request"""
        client = BaseServiceClient("http://localhost:8000")

        with patch.object(client, "_make_request", new_callable=AsyncMock, return_value={}) as mock_request:
            await client.post("/test", data={"key": "val"}, params={"user_id": 1})

        mock_request.assert_called_once_with(
            "POST", "/test", data={"key": "val"}, params={"user_id": 1}
        )

    @pytest.mark.asyncio
    async def test_post_params_default_to_none(self):
        """Verify post() works without params (backward compatible)"""
        client = BaseServiceClient("http://localhost:8000")

        with patch.object(client, "_make_request", new_callable=AsyncMock, return_value={}) as mock_request:
            await client.post("/test", data={"key": "val"})

        mock_request.assert_called_once_with(
            "POST", "/test", data={"key": "val"}, params=None
        )
