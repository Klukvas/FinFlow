"""Tests for shared.clients.subscription.SubscriptionClient.

Covers check_limit, check_modify_allowed, get_read_only_ids,
get_user_features caching, _has_cached, invalidate_cache, and
fail-open behaviour on service errors.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from shared.clients.subscription import SubscriptionClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_feature(
    code: str,
    enabled: bool = True,
    limit_value: int | None = 10,
) -> dict:
    """Build a feature dict matching the subscription-service API shape."""
    return {
        "feature_code": code,
        "enabled": enabled,
        "limit_value": limit_value,
    }


def _ok_response(features: list[dict]) -> MagicMock:
    """Return a mock httpx.Response with status 200 and given features."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = features
    return resp


def _error_response(status_code: int) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = {}
    return resp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client() -> SubscriptionClient:
    """Create a fresh SubscriptionClient with a mocked httpx.Client."""
    with patch.dict("os.environ", {
        "SUBSCRIPTION_SERVICE_URL": "http://test-sub:8080",
        "INTERNAL_SECRET_TOKEN": "test-token",
    }):
        sut = SubscriptionClient(base_url="http://test-sub:8080")
    sut.client = MagicMock(spec=httpx.Client)
    return sut


# ======================================================================
# check_limit
# ======================================================================


class TestCheckLimit:
    """Tests for SubscriptionClient.check_limit."""

    def test_within_limit_returns_true(self, client: SubscriptionClient):
        """User with current_count < limit should be allowed."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
        ])

        can_create, limit = client.check_limit(user_id=1, current_count=3, feature_code="accounts")

        assert can_create is True
        assert limit == 5

    def test_at_limit_returns_false(self, client: SubscriptionClient):
        """User with current_count == limit should be denied."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
        ])

        can_create, limit = client.check_limit(user_id=1, current_count=5, feature_code="accounts")

        assert can_create is False
        assert limit == 5

    def test_over_limit_returns_false(self, client: SubscriptionClient):
        """User with current_count > limit should be denied."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
        ])

        can_create, limit = client.check_limit(user_id=1, current_count=7, feature_code="accounts")

        assert can_create is False
        assert limit == 5

    def test_unlimited_feature_returns_true_none(self, client: SubscriptionClient):
        """Feature with limit_value=None means unlimited."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=None),
        ])

        can_create, limit = client.check_limit(user_id=1, current_count=999, feature_code="accounts")

        assert can_create is True
        assert limit is None

    def test_disabled_feature_returns_false_zero(self, client: SubscriptionClient):
        """Disabled feature should be denied with limit 0."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=False, limit_value=10),
        ])

        can_create, limit = client.check_limit(user_id=1, current_count=0, feature_code="accounts")

        assert can_create is False
        assert limit == 0

    def test_missing_feature_returns_false_zero(self, client: SubscriptionClient):
        """Feature not present in response should be denied."""
        client.client.get.return_value = _ok_response([
            _make_feature("other_feature", enabled=True, limit_value=10),
        ])

        can_create, limit = client.check_limit(user_id=1, current_count=0, feature_code="accounts")

        assert can_create is False
        assert limit == 0

    def test_service_unreachable_fails_open(self, client: SubscriptionClient):
        """Connection error should fail-open: (True, None)."""
        client.client.get.side_effect = httpx.ConnectError("refused")

        can_create, limit = client.check_limit(user_id=1, current_count=100, feature_code="accounts")

        assert can_create is True
        assert limit is None

    def test_timeout_fails_open(self, client: SubscriptionClient):
        """Timeout should fail-open: (True, None)."""
        client.client.get.side_effect = httpx.TimeoutException("timed out")

        can_create, limit = client.check_limit(user_id=1, current_count=100, feature_code="accounts")

        assert can_create is True
        assert limit is None

    def test_retry_on_deny_with_stale_cache(self, client: SubscriptionClient):
        """When denied with a cached result, should invalidate and retry.

        Scenario: cache holds old limit=3, user has 3 records (at limit).
        After cache invalidation the fresh response has limit=10.
        The retry should allow creation.
        """
        old_features = [_make_feature("accounts", enabled=True, limit_value=3)]
        new_features = [_make_feature("accounts", enabled=True, limit_value=10)]

        # Seed the cache with the old (restrictive) limit
        client.client.get.return_value = _ok_response(old_features)
        client.get_user_features(user_id=1)

        # Now the next HTTP call returns a higher limit (plan upgrade)
        client.client.get.return_value = _ok_response(new_features)

        can_create, limit = client.check_limit(user_id=1, current_count=3, feature_code="accounts")

        # First attempt uses cache (limit=3, count=3 -> denied)
        # Retry invalidates cache, fetches fresh (limit=10, count=3 -> allowed)
        assert can_create is True
        assert limit == 10

    def test_no_retry_when_not_cached(self, client: SubscriptionClient):
        """When there is no cached entry, a single deny should be final."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=3),
        ])

        can_create, limit = client.check_limit(user_id=1, current_count=5, feature_code="accounts")

        assert can_create is False
        assert limit == 3
        # Should have made exactly one HTTP call (no retry since no prior cache)
        assert client.client.get.call_count == 1


# ======================================================================
# check_modify_allowed
# ======================================================================


class TestCheckModifyAllowed:
    """Tests for SubscriptionClient.check_modify_allowed."""

    def test_record_within_limit_is_allowed(self, client: SubscriptionClient):
        """Record inside the allowed oldest-N window should be editable."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=3),
        ])
        ordered_ids = [10, 20, 30, 40, 50]  # oldest first

        assert client.check_modify_allowed(
            user_id=1, record_id=10, feature_code="accounts", ordered_record_ids=ordered_ids,
        ) is True

    def test_record_outside_limit_is_denied(self, client: SubscriptionClient):
        """Record beyond the allowed oldest-N window should be read-only."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=3),
        ])
        ordered_ids = [10, 20, 30, 40, 50]

        assert client.check_modify_allowed(
            user_id=1, record_id=40, feature_code="accounts", ordered_record_ids=ordered_ids,
        ) is False

    def test_oldest_n_editable_newest_read_only(self, client: SubscriptionClient):
        """First `limit` records are editable, the rest are not."""
        client.client.get.return_value = _ok_response([
            _make_feature("invoices", enabled=True, limit_value=2),
        ])
        ordered_ids = [1, 2, 3, 4]

        editable = [
            rid for rid in ordered_ids
            if client.check_modify_allowed(
                user_id=1, record_id=rid, feature_code="invoices",
                ordered_record_ids=ordered_ids,
            )
        ]
        read_only = [rid for rid in ordered_ids if rid not in editable]

        assert editable == [1, 2]
        assert read_only == [3, 4]

    def test_unlimited_all_allowed(self, client: SubscriptionClient):
        """Unlimited feature allows modifying any record."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=None),
        ])
        ordered_ids = [1, 2, 3, 4, 5]

        for rid in ordered_ids:
            assert client.check_modify_allowed(
                user_id=1, record_id=rid, feature_code="accounts",
                ordered_record_ids=ordered_ids,
            ) is True

    def test_service_unreachable_fails_open(self, client: SubscriptionClient):
        """Connection error should fail-open: allow modification."""
        client.client.get.side_effect = httpx.ConnectError("refused")

        result = client.check_modify_allowed(
            user_id=1, record_id=99, feature_code="accounts",
            ordered_record_ids=[1, 2, 3, 99],
        )

        assert result is True

    def test_empty_record_list_returns_true(self, client: SubscriptionClient):
        """Empty ordered_record_ids means nothing exceeds the limit."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=3),
        ])

        result = client.check_modify_allowed(
            user_id=1, record_id=1, feature_code="accounts",
            ordered_record_ids=[],
        )

        assert result is True

    def test_disabled_feature_allows_modify(self, client: SubscriptionClient):
        """Disabled or missing feature should fail-open for modify checks."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=False, limit_value=5),
        ])

        result = client.check_modify_allowed(
            user_id=1, record_id=1, feature_code="accounts",
            ordered_record_ids=[1, 2, 3],
        )

        assert result is True

    def test_record_count_equal_to_limit_all_editable(self, client: SubscriptionClient):
        """When len(records) == limit, all records are editable."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=3),
        ])
        ordered_ids = [10, 20, 30]

        for rid in ordered_ids:
            assert client.check_modify_allowed(
                user_id=1, record_id=rid, feature_code="accounts",
                ordered_record_ids=ordered_ids,
            ) is True


# ======================================================================
# get_read_only_ids
# ======================================================================


class TestGetReadOnlyIds:
    """Tests for SubscriptionClient.get_read_only_ids."""

    def test_within_limit_returns_empty_set(self, client: SubscriptionClient):
        """No records exceed the limit when count <= limit."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
        ])

        result = client.get_read_only_ids(
            user_id=1, feature_code="accounts", ordered_record_ids=[1, 2, 3],
        )

        assert result == set()

    def test_over_limit_returns_excess_ids(self, client: SubscriptionClient):
        """Records beyond the limit should be returned as read-only."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=2),
        ])

        result = client.get_read_only_ids(
            user_id=1, feature_code="accounts", ordered_record_ids=[10, 20, 30, 40],
        )

        assert result == {30, 40}

    def test_exactly_at_limit_returns_empty(self, client: SubscriptionClient):
        """When count == limit, nothing is read-only."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=3),
        ])

        result = client.get_read_only_ids(
            user_id=1, feature_code="accounts", ordered_record_ids=[1, 2, 3],
        )

        assert result == set()

    def test_unlimited_returns_empty_set(self, client: SubscriptionClient):
        """Unlimited feature never marks records as read-only."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=None),
        ])

        result = client.get_read_only_ids(
            user_id=1, feature_code="accounts", ordered_record_ids=[1, 2, 3, 4, 5],
        )

        assert result == set()

    def test_service_unreachable_returns_empty_set(self, client: SubscriptionClient):
        """Fail-open: return empty set on connection error."""
        client.client.get.side_effect = httpx.ConnectError("refused")

        result = client.get_read_only_ids(
            user_id=1, feature_code="accounts", ordered_record_ids=[1, 2, 3],
        )

        assert result == set()

    def test_disabled_feature_returns_empty_set(self, client: SubscriptionClient):
        """Disabled feature should not mark anything as read-only."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=False, limit_value=2),
        ])

        result = client.get_read_only_ids(
            user_id=1, feature_code="accounts", ordered_record_ids=[1, 2, 3],
        )

        assert result == set()

    def test_missing_feature_returns_empty_set(self, client: SubscriptionClient):
        """Feature not in response should not mark anything as read-only."""
        client.client.get.return_value = _ok_response([
            _make_feature("other", enabled=True, limit_value=2),
        ])

        result = client.get_read_only_ids(
            user_id=1, feature_code="accounts", ordered_record_ids=[1, 2, 3],
        )

        assert result == set()


# ======================================================================
# Cache behaviour
# ======================================================================


class TestCacheBehaviour:
    """Tests for get_user_features caching and invalidation."""

    def test_cache_hit_within_ttl(self, client: SubscriptionClient):
        """Second call within TTL should not make another HTTP request."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
        ])

        result1 = client.get_user_features(user_id=1)
        result2 = client.get_user_features(user_id=1)

        assert result1 == result2
        assert client.client.get.call_count == 1

    def test_cache_miss_after_ttl_expires(self, client: SubscriptionClient):
        """After TTL expires, a new HTTP request should be made."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
        ])

        client.get_user_features(user_id=1)

        # Manually expire the cache entry
        with client._cache_lock:
            user_id = 1
            features, _ = client._features_cache[user_id]
            client._features_cache[user_id] = (features, time.monotonic() - 1)

        client.get_user_features(user_id=1)

        assert client.client.get.call_count == 2

    def test_invalidate_cache_clears_entry(self, client: SubscriptionClient):
        """invalidate_cache should remove the cache entry entirely."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
        ])

        client.get_user_features(user_id=1)
        assert client._has_cached(user_id=1) is True

        client.invalidate_cache(user_id=1)

        assert client._has_cached(user_id=1) is False

    def test_invalidate_cache_different_user_unaffected(self, client: SubscriptionClient):
        """Invalidating one user should not affect another user's cache."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
        ])

        client.get_user_features(user_id=1)
        client.get_user_features(user_id=2)

        client.invalidate_cache(user_id=1)

        assert client._has_cached(user_id=1) is False
        assert client._has_cached(user_id=2) is True

    def test_5xx_response_returns_none_fail_open(self, client: SubscriptionClient):
        """5xx HTTP status should return None (fail-open), no cache entry."""
        client.client.get.return_value = _error_response(500)

        result = client.get_user_features(user_id=1)

        assert result is None
        # Should NOT be cached (5xx = transient error)
        assert client._has_cached(user_id=1) is False

    def test_503_response_returns_none(self, client: SubscriptionClient):
        """503 Service Unavailable should also return None."""
        client.client.get.return_value = _error_response(503)

        result = client.get_user_features(user_id=1)

        assert result is None
        assert client._has_cached(user_id=1) is False

    def test_4xx_response_returns_empty_dict_cached_briefly(self, client: SubscriptionClient):
        """4xx HTTP status should return {} and cache it briefly."""
        client.client.get.return_value = _error_response(404)

        result = client.get_user_features(user_id=1)

        assert result == {}
        # Should be cached (with short TTL)
        assert client._has_cached(user_id=1) is True

    def test_4xx_cached_value_is_empty_dict(self, client: SubscriptionClient):
        """Second call after 4xx should return cached {} without HTTP call."""
        client.client.get.return_value = _error_response(404)

        client.get_user_features(user_id=1)
        result = client.get_user_features(user_id=1)

        assert result == {}
        assert client.client.get.call_count == 1  # cached, no second call

    def test_successful_response_caches_features_dict(self, client: SubscriptionClient):
        """Cached value should be a dict keyed by feature_code."""
        features = [
            _make_feature("accounts", enabled=True, limit_value=5),
            _make_feature("invoices", enabled=True, limit_value=None),
        ]
        client.client.get.return_value = _ok_response(features)

        result = client.get_user_features(user_id=1)

        assert "accounts" in result
        assert "invoices" in result
        assert result["accounts"]["limit_value"] == 5
        assert result["invoices"]["limit_value"] is None

    def test_connection_error_returns_none_not_cached(self, client: SubscriptionClient):
        """Connection errors should return None and not populate the cache."""
        client.client.get.side_effect = httpx.ConnectError("refused")

        result = client.get_user_features(user_id=1)

        assert result is None
        assert client._has_cached(user_id=1) is False

    def test_generic_exception_returns_none(self, client: SubscriptionClient):
        """Unexpected exceptions should return None (fail-open)."""
        client.client.get.side_effect = RuntimeError("unexpected")

        result = client.get_user_features(user_id=1)

        assert result is None


# ======================================================================
# _has_cached
# ======================================================================


class TestHasCached:
    """Tests for SubscriptionClient._has_cached."""

    def test_returns_true_for_live_entry(self, client: SubscriptionClient):
        """Should return True when a non-expired entry exists."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
        ])
        client.get_user_features(user_id=1)

        assert client._has_cached(user_id=1) is True

    def test_returns_false_for_expired_entry(self, client: SubscriptionClient):
        """Should return False when the entry has expired."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
        ])
        client.get_user_features(user_id=1)

        # Force expiration
        with client._cache_lock:
            features, _ = client._features_cache[1]
            client._features_cache[1] = (features, time.monotonic() - 1)

        assert client._has_cached(user_id=1) is False

    def test_returns_false_for_missing_entry(self, client: SubscriptionClient):
        """Should return False when no entry exists at all."""
        assert client._has_cached(user_id=999) is False

    def test_returns_true_for_4xx_cached_entry(self, client: SubscriptionClient):
        """4xx responses produce a cached {} entry that counts as cached."""
        client.client.get.return_value = _error_response(404)
        client.get_user_features(user_id=1)

        assert client._has_cached(user_id=1) is True


# ======================================================================
# get_feature_limit
# ======================================================================


class TestGetFeatureLimit:
    """Tests for SubscriptionClient.get_feature_limit."""

    def test_returns_limit_value(self, client: SubscriptionClient):
        client.client.get.return_value = _ok_response([
            _make_feature("workspaces", enabled=True, limit_value=3),
        ])

        result = client.get_feature_limit(user_id=1, feature_code="workspaces")

        assert result == 3

    def test_returns_none_for_unlimited(self, client: SubscriptionClient):
        client.client.get.return_value = _ok_response([
            _make_feature("workspaces", enabled=True, limit_value=None),
        ])

        result = client.get_feature_limit(user_id=1, feature_code="workspaces")

        assert result is None

    def test_returns_zero_for_disabled(self, client: SubscriptionClient):
        client.client.get.return_value = _ok_response([
            _make_feature("workspaces", enabled=False, limit_value=10),
        ])

        result = client.get_feature_limit(user_id=1, feature_code="workspaces")

        assert result == 0

    def test_returns_none_when_unreachable(self, client: SubscriptionClient):
        client.client.get.side_effect = httpx.ConnectError("refused")

        result = client.get_feature_limit(user_id=1, feature_code="workspaces")

        assert result is None


# ======================================================================
# set_basic_plan
# ======================================================================


class TestSetBasicPlan:
    """Tests for SubscriptionClient.set_basic_plan."""

    def test_sends_correct_request(self, client: SubscriptionClient):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        client.client.post.return_value = resp

        client.set_basic_plan(user_id=42, plan_code="basic")

        client.client.post.assert_called_once()
        call_kwargs = client.client.post.call_args
        assert "/v1/subscriptions/42:set_plan" in call_kwargs.args[0]
        assert call_kwargs.kwargs["json"] == {"plan_code": "basic"}
        assert "Idempotency-Key" in call_kwargs.kwargs["headers"]

    def test_custom_plan_code(self, client: SubscriptionClient):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 200
        client.client.post.return_value = resp

        client.set_basic_plan(user_id=1, plan_code="starter")

        call_kwargs = client.client.post.call_args
        assert call_kwargs.kwargs["json"] == {"plan_code": "starter"}

    def test_does_not_raise_on_connection_error(self, client: SubscriptionClient):
        """set_basic_plan should swallow connection errors gracefully."""
        client.client.post.side_effect = httpx.ConnectError("refused")

        # Should not raise
        client.set_basic_plan(user_id=1)

    def test_does_not_raise_on_4xx(self, client: SubscriptionClient):
        """set_basic_plan should log but not raise on 4xx."""
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = 422
        client.client.post.return_value = resp

        # Should not raise
        client.set_basic_plan(user_id=1)

    def test_does_not_raise_on_timeout(self, client: SubscriptionClient):
        client.client.post.side_effect = httpx.TimeoutException("timed out")

        # Should not raise
        client.set_basic_plan(user_id=1)


# ======================================================================
# Headers / constructor
# ======================================================================


class TestConstructorAndHeaders:
    """Tests for __init__ and _get_headers."""

    def test_default_base_url_from_env(self):
        with patch.dict("os.environ", {"SUBSCRIPTION_SERVICE_URL": "http://custom:9090"}):
            sut = SubscriptionClient()
            assert sut.base_url == "http://custom:9090"
            sut.close()

    def test_base_url_strips_trailing_slash(self):
        sut = SubscriptionClient(base_url="http://test:8080/")
        assert sut.base_url == "http://test:8080"
        sut.close()

    def test_headers_include_internal_token(self):
        with patch.dict("os.environ", {"INTERNAL_SECRET_TOKEN": "secret123"}):
            sut = SubscriptionClient(base_url="http://test:8080")
            headers = sut._get_headers()
            assert headers["X-Internal-Token"] == "secret123"
            sut.close()

    def test_headers_without_token(self):
        with patch.dict("os.environ", {"INTERNAL_SECRET_TOKEN": ""}, clear=False):
            sut = SubscriptionClient(base_url="http://test:8080")
            headers = sut._get_headers()
            assert "X-Internal-Token" not in headers
            sut.close()

    def test_get_instance_returns_singleton(self):
        """get_instance should return the same object on repeated calls."""
        # Reset the module-level singleton
        import shared.clients.subscription as mod
        original = mod._instance
        mod._instance = None
        try:
            inst1 = SubscriptionClient.get_instance()
            inst2 = SubscriptionClient.get_instance()
            assert inst1 is inst2
        finally:
            mod._instance = original
            inst1.close()


# ======================================================================
# Edge cases / integration-style
# ======================================================================


class TestEdgeCases:
    """Miscellaneous edge cases."""

    def test_check_limit_with_zero_current_count(self, client: SubscriptionClient):
        """Zero records and positive limit should allow creation."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
        ])

        can_create, limit = client.check_limit(user_id=1, current_count=0, feature_code="accounts")

        assert can_create is True
        assert limit == 5

    def test_check_limit_with_limit_value_zero(self, client: SubscriptionClient):
        """Feature with limit_value=0 should deny even at count 0."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=0),
        ])

        can_create, limit = client.check_limit(user_id=1, current_count=0, feature_code="accounts")

        assert can_create is False
        assert limit == 0

    def test_get_read_only_ids_preserves_order(self, client: SubscriptionClient):
        """Read-only IDs should be the *last* N (newest) records."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=2),
        ])

        result = client.get_read_only_ids(
            user_id=1, feature_code="accounts",
            ordered_record_ids=["a", "b", "c", "d", "e"],
        )

        assert result == {"c", "d", "e"}

    def test_multiple_features_in_response(self, client: SubscriptionClient):
        """Multiple features should each be independently accessible."""
        client.client.get.return_value = _ok_response([
            _make_feature("accounts", enabled=True, limit_value=5),
            _make_feature("invoices", enabled=True, limit_value=100),
            _make_feature("reports", enabled=False, limit_value=10),
        ])

        can_accounts, lim_accounts = client.check_limit(user_id=1, current_count=3, feature_code="accounts")
        can_invoices, lim_invoices = client.check_limit(user_id=1, current_count=50, feature_code="invoices")
        can_reports, lim_reports = client.check_limit(user_id=1, current_count=0, feature_code="reports")

        assert can_accounts is True
        assert lim_accounts == 5
        assert can_invoices is True
        assert lim_invoices == 100
        assert can_reports is False
        assert lim_reports == 0

    def test_different_users_have_independent_caches(self, client: SubscriptionClient):
        """User 1 and User 2 should have separate cache entries."""
        resp_user1 = _ok_response([_make_feature("accounts", enabled=True, limit_value=5)])
        resp_user2 = _ok_response([_make_feature("accounts", enabled=True, limit_value=20)])

        client.client.get.return_value = resp_user1
        features1 = client.get_user_features(user_id=1)

        client.client.get.return_value = resp_user2
        features2 = client.get_user_features(user_id=2)

        assert features1["accounts"]["limit_value"] == 5
        assert features2["accounts"]["limit_value"] == 20

    def test_close_closes_httpx_client(self, client: SubscriptionClient):
        """close() should delegate to the underlying httpx client."""
        client.close()
        client.client.close.assert_called_once()
