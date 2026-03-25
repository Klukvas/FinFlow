"""Tests for utility modules: admin_guard, consent, errors, idempotency, jwt, rate_limit."""

from __future__ import annotations

import time
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, AsyncMock
from uuid import uuid4

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from payment_service.app.utils.errors import (
    ServiceError,
    AuthError,
    NotFoundError,
    ValidationError,
    ConflictError,
    service_exception_handler,
    unhandled_exception_handler,
)
from payment_service.app.utils.consent import (
    validate_subscription_consent,
    get_current_consent_version,
    CURRENT_CONSENT_VERSION,
    MAX_CONSENT_AGE_SECONDS,
)
from payment_service.app.utils.idempotency import (
    compute_request_hash,
    check_idempotency,
    store_idempotency,
    get_idempotency_key,
)


# ======================================================================
# errors.py
# ======================================================================


class TestServiceError:
    """Tests for the ServiceError hierarchy."""

    def test_service_error_attributes(self):
        err = ServiceError(
            message="Something went wrong",
            error_code="@test/ERROR",
            status_code=400,
            details={"key": "value"},
        )
        assert err.message == "Something went wrong"
        assert err.error_code == "@test/ERROR"
        assert err.status_code == 400
        assert err.details == {"key": "value"}
        assert str(err) == "Something went wrong"

    def test_service_error_default_status(self):
        err = ServiceError(message="bad", error_code="@test/BAD")
        assert err.status_code == 400

    def test_service_error_default_details(self):
        err = ServiceError(message="bad", error_code="@test/BAD")
        assert err.details == {}

    def test_auth_error_status_401(self):
        err = AuthError(message="Unauthorized", error_code="@test/AUTH")
        assert err.status_code == status.HTTP_401_UNAUTHORIZED

    def test_not_found_error_status_404(self):
        err = NotFoundError(message="Not found", error_code="@test/NOT_FOUND")
        assert err.status_code == status.HTTP_404_NOT_FOUND

    def test_validation_error_status_400(self):
        err = ValidationError(message="Invalid", error_code="@test/INVALID")
        assert err.status_code == status.HTTP_400_BAD_REQUEST

    def test_conflict_error_status_409(self):
        err = ConflictError(message="Conflict", error_code="@test/CONFLICT")
        assert err.status_code == status.HTTP_409_CONFLICT

    def test_auth_error_with_details(self):
        err = AuthError(
            message="Token expired",
            error_code="@test/EXPIRED",
            details={"token_age": 3600},
        )
        assert err.details["token_age"] == 3600

    def test_errors_are_exceptions(self):
        for cls in (ServiceError, AuthError, NotFoundError, ValidationError, ConflictError):
            assert issubclass(cls, Exception)


class TestServiceExceptionHandler:
    """Tests for the service_exception_handler function."""

    @pytest.mark.asyncio
    async def test_returns_json_response_with_error_info(self):
        mock_request = MagicMock()
        mock_request.url.path = "/test"

        exc = ValidationError(
            message="Field is required",
            error_code="@test/REQUIRED",
            details={"field": "name"},
        )

        response = await service_exception_handler(mock_request, exc)

        assert response.status_code == 400
        import json
        body = json.loads(response.body)
        assert body["error"] == "@test/REQUIRED"
        assert body["message"] == "Field is required"
        assert body["details"]["field"] == "name"


class TestUnhandledExceptionHandler:
    """Tests for the unhandled_exception_handler function."""

    @pytest.mark.asyncio
    async def test_returns_500_with_generic_message(self):
        mock_request = MagicMock()
        mock_request.url.path = "/broken"

        exc = RuntimeError("unexpected crash")

        response = await unhandled_exception_handler(mock_request, exc)

        assert response.status_code == 500
        import json
        body = json.loads(response.body)
        assert body["error"] == "@payment_service/INTERNAL_ERROR"
        # The generic message does not include the original exception message
        assert "crash" not in body["message"]


# ======================================================================
# consent.py
# ======================================================================


class TestValidateSubscriptionConsent:
    """Tests for validate_subscription_consent."""

    def _valid_metadata(self) -> dict:
        return {
            "consent_given": True,
            "consent_version": CURRENT_CONSENT_VERSION,
            "consent_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def test_valid_consent_passes(self):
        """Valid consent metadata must not raise."""
        validate_subscription_consent(self._valid_metadata())

    def test_none_metadata_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_subscription_consent(None)
        assert "METADATA_REQUIRED" in exc_info.value.error_code

    def test_empty_dict_raises_metadata_required(self):
        """Empty dict is falsy in Python, so triggers METADATA_REQUIRED."""
        with pytest.raises(ValidationError) as exc_info:
            validate_subscription_consent({})
        assert "METADATA_REQUIRED" in exc_info.value.error_code

    def test_consent_given_missing_raises_consent_required(self):
        """Dict with keys but no consent_given triggers CONSENT_REQUIRED."""
        with pytest.raises(ValidationError) as exc_info:
            validate_subscription_consent({"some_key": "some_value"})
        assert "CONSENT_REQUIRED" in exc_info.value.error_code

    def test_consent_given_false_raises(self):
        meta = self._valid_metadata()
        meta["consent_given"] = False
        with pytest.raises(ValidationError) as exc_info:
            validate_subscription_consent(meta)
        assert "CONSENT_REQUIRED" in exc_info.value.error_code

    def test_missing_consent_version_raises(self):
        meta = self._valid_metadata()
        del meta["consent_version"]
        with pytest.raises(ValidationError) as exc_info:
            validate_subscription_consent(meta)
        assert "CONSENT_VERSION_REQUIRED" in exc_info.value.error_code

    def test_wrong_consent_version_raises(self):
        meta = self._valid_metadata()
        meta["consent_version"] = "v0.0.1"
        with pytest.raises(ValidationError) as exc_info:
            validate_subscription_consent(meta)
        assert "CONSENT_VERSION_MISMATCH" in exc_info.value.error_code

    def test_expired_consent_timestamp_raises(self):
        meta = self._valid_metadata()
        old_time = datetime.now(timezone.utc) - timedelta(seconds=MAX_CONSENT_AGE_SECONDS + 60)
        meta["consent_timestamp"] = old_time.isoformat()
        with pytest.raises(ValidationError) as exc_info:
            validate_subscription_consent(meta)
        assert "CONSENT_EXPIRED" in exc_info.value.error_code

    def test_future_consent_timestamp_raises(self):
        meta = self._valid_metadata()
        future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        meta["consent_timestamp"] = future_time.isoformat()
        with pytest.raises(ValidationError) as exc_info:
            validate_subscription_consent(meta)
        assert "CONSENT_FUTURE_TIMESTAMP" in exc_info.value.error_code

    def test_invalid_timestamp_format_raises(self):
        meta = self._valid_metadata()
        meta["consent_timestamp"] = "not-a-date"
        with pytest.raises(ValidationError) as exc_info:
            validate_subscription_consent(meta)
        assert "INVALID_TIMESTAMP" in exc_info.value.error_code

    def test_consent_without_timestamp_passes(self):
        """If no consent_timestamp is provided, timestamp validation is skipped."""
        meta = {
            "consent_given": True,
            "consent_version": CURRENT_CONSENT_VERSION,
        }
        # Should not raise
        validate_subscription_consent(meta)

    def test_z_suffix_timestamp_accepted(self):
        """ISO timestamps with Z suffix must be accepted."""
        meta = self._valid_metadata()
        meta["consent_timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        validate_subscription_consent(meta)


class TestGetCurrentConsentVersion:
    """Tests for get_current_consent_version."""

    def test_returns_current_version(self):
        assert get_current_consent_version() == CURRENT_CONSENT_VERSION

    def test_returns_string(self):
        assert isinstance(get_current_consent_version(), str)


# ======================================================================
# idempotency.py
# ======================================================================


class TestComputeRequestHash:
    """Tests for compute_request_hash."""

    def test_same_body_same_hash(self):
        body = {"user_id": "u1", "amount": "10.00"}
        h1 = compute_request_hash(body)
        h2 = compute_request_hash(body)
        assert h1 == h2

    def test_different_body_different_hash(self):
        h1 = compute_request_hash({"user_id": "u1"})
        h2 = compute_request_hash({"user_id": "u2"})
        assert h1 != h2

    def test_key_order_does_not_matter(self):
        """JSON is sorted by keys, so order must not affect the hash."""
        h1 = compute_request_hash({"a": 1, "b": 2})
        h2 = compute_request_hash({"b": 2, "a": 1})
        assert h1 == h2

    def test_returns_sha256_hex(self):
        h = compute_request_hash({"key": "value"})
        assert len(h) == 64  # SHA-256 hex digest length
        assert all(c in "0123456789abcdef" for c in h)


class TestCheckIdempotency:
    """Tests for check_idempotency."""

    def test_returns_none_when_no_existing_key(self, mock_db):
        result = check_idempotency(mock_db, "key_1", "scope_1", "hash_1")
        assert result is None

    def test_returns_cached_response_on_hit(self, mock_db):
        cached_response = {"payment_id": "test", "status": "CREATED"}

        existing_key = MagicMock()
        existing_key.request_hash = "hash_match"
        existing_key.response_body = cached_response

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = existing_key
        mock_db.query.return_value = query_mock

        result = check_idempotency(mock_db, "key_match", "scope_1", "hash_match")
        assert result == cached_response

    def test_raises_conflict_on_hash_mismatch(self, mock_db):
        existing_key = MagicMock()
        existing_key.request_hash = "hash_original"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = existing_key
        mock_db.query.return_value = query_mock

        with pytest.raises(ConflictError) as exc_info:
            check_idempotency(mock_db, "key_conflict", "scope_1", "hash_different")
        assert "IDEMPOTENCY_CONFLICT" in exc_info.value.error_code


class TestStoreIdempotency:
    """Tests for store_idempotency."""

    @patch("payment_service.app.utils.idempotency.settings")
    def test_adds_and_commits(self, mock_settings, mock_db):
        mock_settings.idempotency_ttl_seconds = 86400

        store_idempotency(
            mock_db, "key_store", "scope_1", "hash_1",
            {"response": "data"}, "201",
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("payment_service.app.utils.idempotency.settings")
    def test_no_commit_when_auto_commit_false(self, mock_settings, mock_db):
        mock_settings.idempotency_ttl_seconds = 86400

        store_idempotency(
            mock_db, "key_no_commit", "scope_1", "hash_1",
            {"response": "data"}, "201",
            auto_commit=False,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_not_called()

    @patch("payment_service.app.utils.idempotency.settings")
    def test_stores_correct_key_record(self, mock_settings, mock_db):
        mock_settings.idempotency_ttl_seconds = 3600

        store_idempotency(
            mock_db, "key_check", "create_payment", "hash_abc",
            {"payment_id": "p1"}, "201",
        )

        added_obj = mock_db.add.call_args.args[0]
        assert added_obj.key == "key_check"
        assert added_obj.scope == "create_payment"
        assert added_obj.request_hash == "hash_abc"
        assert added_obj.response_body == {"payment_id": "p1"}
        assert added_obj.response_status == "201"


class TestGetIdempotencyKey:
    """Tests for get_idempotency_key dependency."""

    @pytest.mark.asyncio
    async def test_returns_header_value(self):
        mock_request = MagicMock()
        result = await get_idempotency_key(mock_request, idempotency_key="my-key")
        assert result == "my-key"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_header(self):
        mock_request = MagicMock()
        result = await get_idempotency_key(mock_request, idempotency_key=None)
        assert result is None


# ======================================================================
# admin_guard.py
# ======================================================================


class TestVerifyAdminToken:
    """Tests for verify_admin_token."""

    @patch("payment_service.app.utils.admin_guard.settings")
    def test_missing_auth_header_raises_401(self, mock_settings):
        from payment_service.app.utils.admin_guard import verify_admin_token

        mock_request = MagicMock()
        mock_request.headers.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(mock_request)
        assert exc_info.value.status_code == 401

    @patch("payment_service.app.utils.admin_guard.settings")
    def test_invalid_token_format_raises_401(self, mock_settings):
        from payment_service.app.utils.admin_guard import verify_admin_token

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "InvalidFormat"

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(mock_request)
        assert exc_info.value.status_code == 401

    @patch("payment_service.app.utils.admin_guard.settings")
    def test_no_jwt_secret_raises_500(self, mock_settings):
        from payment_service.app.utils.admin_guard import verify_admin_token

        mock_settings.jwt_secret_key = ""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer some-token"

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(mock_request)
        assert exc_info.value.status_code == 500

    @patch("payment_service.app.utils.admin_guard.settings")
    @patch("payment_service.app.utils.admin_guard.jwt.decode")
    def test_non_admin_role_raises_403(self, mock_decode, mock_settings):
        from payment_service.app.utils.admin_guard import verify_admin_token

        mock_settings.jwt_secret_key = "secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_decode.return_value = {"sub": "user_1", "role": "user"}

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer valid-token"

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(mock_request)
        assert exc_info.value.status_code == 403

    @patch("payment_service.app.utils.admin_guard.settings")
    @patch("payment_service.app.utils.admin_guard.jwt.decode")
    def test_valid_admin_token_returns_payload(self, mock_decode, mock_settings):
        from payment_service.app.utils.admin_guard import verify_admin_token

        mock_settings.jwt_secret_key = "secret"
        mock_settings.jwt_algorithm = "HS256"
        expected_payload = {"sub": "admin_1", "role": "admin"}
        mock_decode.return_value = expected_payload

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer admin-token"

        result = verify_admin_token(mock_request)
        assert result == expected_payload

    @patch("payment_service.app.utils.admin_guard.settings")
    @patch("payment_service.app.utils.admin_guard.jwt.decode")
    def test_expired_token_raises_401(self, mock_decode, mock_settings):
        import jwt as real_jwt
        from payment_service.app.utils.admin_guard import verify_admin_token

        mock_settings.jwt_secret_key = "secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_decode.side_effect = real_jwt.ExpiredSignatureError()

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer expired-token"

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(mock_request)
        assert exc_info.value.status_code == 401

    @patch("payment_service.app.utils.admin_guard.settings")
    @patch("payment_service.app.utils.admin_guard.jwt.decode")
    def test_invalid_token_raises_401(self, mock_decode, mock_settings):
        import jwt as real_jwt
        from payment_service.app.utils.admin_guard import verify_admin_token

        mock_settings.jwt_secret_key = "secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_decode.side_effect = real_jwt.InvalidTokenError("bad token")

        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer bad-token"

        with pytest.raises(HTTPException) as exc_info:
            verify_admin_token(mock_request)
        assert exc_info.value.status_code == 401


# ======================================================================
# jwt.py
# ======================================================================


class TestVerifyJwtToken:
    """Tests for verify_jwt_token and JWTPayload."""

    @patch("payment_service.app.utils.jwt.settings")
    @patch("payment_service.app.utils.jwt.jwt.decode")
    def test_valid_token_returns_payload(self, mock_decode, mock_settings):
        from payment_service.app.utils.jwt import verify_jwt_token, JWTPayload

        mock_settings.jwt_secret_key = "secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_decode.return_value = {
            "sub": 42,
            "email": "user@example.com",
            "workspace_id": 7,
        }

        result = verify_jwt_token("Bearer valid-token")

        assert isinstance(result, JWTPayload)
        assert result.user_id == "42"
        assert result.email == "user@example.com"
        assert result.workspace_id == "7"

    @patch("payment_service.app.utils.jwt.settings")
    @patch("payment_service.app.utils.jwt.jwt.decode")
    def test_workspace_id_none_when_absent(self, mock_decode, mock_settings):
        from payment_service.app.utils.jwt import verify_jwt_token

        mock_settings.jwt_secret_key = "secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_decode.return_value = {"sub": 1, "email": "a@b.com"}

        result = verify_jwt_token("Bearer token")
        assert result.workspace_id is None

    def test_missing_auth_header_raises(self):
        from payment_service.app.utils.jwt import verify_jwt_token

        with pytest.raises(AuthError) as exc_info:
            verify_jwt_token("")
        assert "MISSING_AUTH_HEADER" in exc_info.value.error_code

    def test_invalid_format_raises(self):
        from payment_service.app.utils.jwt import verify_jwt_token

        with pytest.raises(AuthError) as exc_info:
            verify_jwt_token("InvalidFormat")
        assert "INVALID_AUTH_FORMAT" in exc_info.value.error_code

    def test_basic_auth_format_raises(self):
        from payment_service.app.utils.jwt import verify_jwt_token

        with pytest.raises(AuthError) as exc_info:
            verify_jwt_token("Basic dXNlcjpwYXNz")
        assert "INVALID_AUTH_FORMAT" in exc_info.value.error_code

    @patch("payment_service.app.utils.jwt.settings")
    @patch("payment_service.app.utils.jwt.jwt.decode")
    def test_expired_token_raises_auth_error(self, mock_decode, mock_settings):
        import jwt as real_jwt
        from payment_service.app.utils.jwt import verify_jwt_token

        mock_settings.jwt_secret_key = "secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_decode.side_effect = real_jwt.ExpiredSignatureError()

        with pytest.raises(AuthError) as exc_info:
            verify_jwt_token("Bearer expired")
        assert "TOKEN_EXPIRED" in exc_info.value.error_code

    @patch("payment_service.app.utils.jwt.settings")
    @patch("payment_service.app.utils.jwt.jwt.decode")
    def test_invalid_token_raises_auth_error(self, mock_decode, mock_settings):
        import jwt as real_jwt
        from payment_service.app.utils.jwt import verify_jwt_token

        mock_settings.jwt_secret_key = "secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_decode.side_effect = real_jwt.InvalidTokenError("corrupt")

        with pytest.raises(AuthError) as exc_info:
            verify_jwt_token("Bearer corrupt")
        assert "INVALID_TOKEN" in exc_info.value.error_code


class TestJWTPayload:
    """Tests for JWTPayload class."""

    def test_attributes_set_correctly(self):
        from payment_service.app.utils.jwt import JWTPayload

        payload = JWTPayload(user_id="u1", email="test@test.com", workspace_id="ws_1")
        assert payload.user_id == "u1"
        assert payload.email == "test@test.com"
        assert payload.workspace_id == "ws_1"

    def test_workspace_id_defaults_none(self):
        from payment_service.app.utils.jwt import JWTPayload

        payload = JWTPayload(user_id="u1", email="test@test.com")
        assert payload.workspace_id is None


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    def test_returns_token_payload_as_is(self):
        from payment_service.app.utils.jwt import get_current_user, JWTPayload

        payload = JWTPayload(user_id="u1", email="t@t.com")
        result = get_current_user(payload)
        assert result is payload


# ======================================================================
# rate_limit.py
# ======================================================================


class TestCheckRateLimit:
    """Tests for check_rate_limit."""

    def test_within_limit_returns_true(self):
        from payment_service.app.utils.rate_limit import check_rate_limit

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1

        result = check_rate_limit(mock_redis, "rate:test:user1", 5, 60)
        assert result is True
        mock_redis.expire.assert_called_once_with("rate:test:user1", 60)

    def test_at_limit_returns_true(self):
        from payment_service.app.utils.rate_limit import check_rate_limit

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 5

        result = check_rate_limit(mock_redis, "rate:test:user1", 5, 60)
        assert result is True

    def test_over_limit_returns_false(self):
        from payment_service.app.utils.rate_limit import check_rate_limit

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 6

        result = check_rate_limit(mock_redis, "rate:test:user1", 5, 60)
        assert result is False

    def test_first_request_sets_expire(self):
        from payment_service.app.utils.rate_limit import check_rate_limit

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1

        check_rate_limit(mock_redis, "rate:key", 10, 120)
        mock_redis.expire.assert_called_once_with("rate:key", 120)

    def test_subsequent_request_does_not_set_expire(self):
        from payment_service.app.utils.rate_limit import check_rate_limit

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 3

        check_rate_limit(mock_redis, "rate:key", 10, 120)
        mock_redis.expire.assert_not_called()


class TestRequirePaymentRateLimit:
    """Tests for require_payment_rate_limit dependency."""

    @pytest.mark.asyncio
    @patch("payment_service.app.utils.rate_limit._get_redis")
    async def test_within_limit_passes(self, mock_get_redis):
        from payment_service.app.utils.rate_limit import require_payment_rate_limit
        from payment_service.app.utils.jwt import JWTPayload

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1
        mock_get_redis.return_value = mock_redis

        user = JWTPayload(user_id="u1", email="t@t.com")

        # Should not raise
        await require_payment_rate_limit(current_user=user)

    @pytest.mark.asyncio
    @patch("payment_service.app.utils.rate_limit._get_redis")
    async def test_over_limit_raises_429(self, mock_get_redis):
        from payment_service.app.utils.rate_limit import require_payment_rate_limit
        from payment_service.app.utils.jwt import JWTPayload

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 100  # Way over limit
        mock_get_redis.return_value = mock_redis

        user = JWTPayload(user_id="u_limited", email="t@t.com")

        with pytest.raises(HTTPException) as exc_info:
            await require_payment_rate_limit(current_user=user)
        assert exc_info.value.status_code == 429
