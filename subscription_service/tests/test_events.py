"""Tests for EventBus."""

from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock

from app.services.events import EventBus


class TestEventBus:
    """Tests for EventBus.publish_subscription_changed."""

    def test_publishes_event_to_redis(self, mock_redis):
        """Must publish event JSON to the correct Redis channel."""
        bus = EventBus(redis_client=mock_redis)
        bus.publish_subscription_changed(
            user_id="user_1",
            plan_code="professional",
            status="active",
            expires_at="2025-06-01T00:00:00",
            version=2,
        )

        mock_redis.publish.assert_called_once()
        channel, payload_str = mock_redis.publish.call_args[0]
        assert channel == "user.subscription.changed"

        payload = json.loads(payload_str)
        assert payload["user_id"] == "user_1"
        assert payload["plan_code"] == "professional"
        assert payload["status"] == "active"
        assert payload["expires_at"] == "2025-06-01T00:00:00"
        assert payload["version"] == 2

    def test_publishes_with_empty_expires_at(self, mock_redis):
        """Must handle empty expires_at."""
        bus = EventBus(redis_client=mock_redis)
        bus.publish_subscription_changed(
            user_id="user_1",
            plan_code="free",
            status="canceled",
            expires_at="",
            version=1,
        )

        payload = json.loads(mock_redis.publish.call_args[0][1])
        assert payload["expires_at"] == ""
