"""Tests for IdempotencyStore."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.utils.idempotency import IdempotencyStore


class TestIdempotencyStore:
    """Tests for IdempotencyStore.check_and_set."""

    def test_first_call_returns_true(self, mock_redis):
        """First call with a key must succeed (return True)."""
        pipeline = MagicMock()
        pipeline.get.return_value = None
        mock_redis.pipeline.return_value = pipeline
        pipeline.__enter__ = MagicMock(return_value=pipeline)
        pipeline.__exit__ = MagicMock(return_value=False)

        store = IdempotencyStore(redis_client=mock_redis)
        result = store.check_and_set("key_1", "value_1")

        assert result is True

    def test_duplicate_same_value_returns_true(self, mock_redis):
        """Duplicate call with same value must return True (idempotent)."""
        pipeline = MagicMock()
        pipeline.get.return_value = "value_1"
        mock_redis.pipeline.return_value = pipeline
        pipeline.__enter__ = MagicMock(return_value=pipeline)
        pipeline.__exit__ = MagicMock(return_value=False)

        store = IdempotencyStore(redis_client=mock_redis)
        result = store.check_and_set("key_1", "value_1")

        assert result is True

    def test_duplicate_different_value_returns_false(self, mock_redis):
        """Duplicate call with different value must return False (conflict)."""
        pipeline = MagicMock()
        pipeline.get.return_value = "original_value"
        mock_redis.pipeline.return_value = pipeline
        pipeline.__enter__ = MagicMock(return_value=pipeline)
        pipeline.__exit__ = MagicMock(return_value=False)

        store = IdempotencyStore(redis_client=mock_redis)
        result = store.check_and_set("key_1", "different_value")

        assert result is False
