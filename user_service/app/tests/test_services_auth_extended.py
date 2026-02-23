"""
Extended tests for app/services/auth.py to cover uncovered lines.
Covers: 68% -> target 80%+
Uncovered lines: 38-40, 47, 49-53, 112-115, 124-125, 141-142, 159-166,
                 207-209, 233-235, 239-250, 269-278, 285-291, 294-296, 328-331
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError
from jose import jwt
from datetime import datetime, timedelta, timezone

from app.services.auth import AuthService
from app.exceptions.user_errors import (
    UserNotFoundError,
    UserValidationError,
    UserAuthenticationError,
    UserRegistrationError,
    PasswordPolicyError,
)
from app.config import settings


# ---------------------------------------------------------------------------
# Helpers: build a minimal Session mock
# ---------------------------------------------------------------------------

def _make_db():
    """Return a MagicMock that acts like a SQLAlchemy session."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    return db


def _make_user(user_id: int = 1, email: str = "user@test.com", role: str = "user"):
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.role = role
    user.status = "active"
    user.hashed_password = _hash("OldPass123!")
    user.default_workspace_id = None
    user.base_currency = "USD"
    return user


def _hash(pw: str) -> str:
    from passlib.hash import bcrypt
    return bcrypt.hash(pw)


# ---------------------------------------------------------------------------
# get_user_by_email
# ---------------------------------------------------------------------------

class TestGetUserByEmail:
    def test_returns_none_when_not_found(self):
        db = _make_db()
        service = AuthService(db)
        result = service.get_user_by_email("nobody@test.com")
        assert result is None

    def test_raises_validation_error_on_db_exception(self):
        """Lines 38-40: DB error during get_user_by_email raises UserValidationError."""
        db = MagicMock()
        db.query.side_effect = RuntimeError("db failure")
        service = AuthService(db)

        with pytest.raises(UserValidationError):
            service.get_user_by_email("x@test.com")


# ---------------------------------------------------------------------------
# get_user_by_id
# ---------------------------------------------------------------------------

class TestGetUserById:
    def test_raises_not_found_for_missing_id(self):
        """Line 47: UserNotFoundError raised when user is None."""
        db = _make_db()
        service = AuthService(db)

        with pytest.raises(UserNotFoundError):
            service.get_user_by_id(99999)

    def test_raises_validation_error_on_db_exception(self):
        """Lines 49-53: DB error propagates as UserValidationError."""
        db = MagicMock()
        db.query.side_effect = RuntimeError("connection dropped")
        service = AuthService(db)

        with pytest.raises(UserValidationError):
            service.get_user_by_id(1)


# ---------------------------------------------------------------------------
# create_user – workspace and subscription paths
# ---------------------------------------------------------------------------

class TestCreateUserWorkspaceSubscription:
    """Lines 112-115, 124-125, 141-142, 159-166"""

    def test_workspace_created_and_linked(self):
        """When workspace client returns a UUID the user is updated."""
        from uuid import UUID

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None  # no existing user

        workspace_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch("app.clients.currency.CurrencyClient.validate_currency", return_value=True), \
             patch("app.clients.workspace.WorkspaceClient.create_personal_workspace", return_value=workspace_id), \
             patch("app.clients.subscription.SubscriptionClient.set_basic_plan"):
            from app.schemas.user import UserCreate
            service = AuthService(db)
            data = UserCreate(email="ws_linked@test.com", password="WsPass123!")
            user = service.create_user(data)

        # db.commit should have been called (workspace link)
        assert db.commit.called

    def test_workspace_returns_none_logs_warning(self):
        """When workspace client returns None, no link is made."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.clients.currency.CurrencyClient.validate_currency", return_value=True), \
             patch("app.clients.workspace.WorkspaceClient.create_personal_workspace", return_value=None), \
             patch("app.clients.subscription.SubscriptionClient.set_basic_plan"):
            from app.schemas.user import UserCreate
            service = AuthService(db)
            data = UserCreate(email="ws_none@test.com", password="WsPass123!")
            user = service.create_user(data)

        # Should still return a user even without workspace
        assert user is not None

    def test_workspace_exception_does_not_block_registration(self):
        """Line 124-125: workspace exception is swallowed (best-effort)."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.clients.currency.CurrencyClient.validate_currency", return_value=True), \
             patch("app.clients.workspace.WorkspaceClient.create_personal_workspace", side_effect=Exception("ws down")), \
             patch("app.clients.subscription.SubscriptionClient.set_basic_plan"):
            from app.schemas.user import UserCreate
            service = AuthService(db)
            data = UserCreate(email="ws_err@test.com", password="WsPass123!")
            user = service.create_user(data)

        assert user is not None

    def test_subscription_exception_does_not_block_registration(self):
        """Lines 141-142: subscription exception is swallowed (best-effort)."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.clients.currency.CurrencyClient.validate_currency", return_value=True), \
             patch("app.clients.workspace.WorkspaceClient.create_personal_workspace", return_value=None), \
             patch("app.clients.subscription.SubscriptionClient.set_basic_plan", side_effect=Exception("sub down")):
            from app.schemas.user import UserCreate
            service = AuthService(db)
            data = UserCreate(email="sub_err@test.com", password="WsPass123!")
            user = service.create_user(data)

        assert user is not None

    def test_integrity_error_raises_registration_error(self):
        """Lines 159-162: IntegrityError from DB is caught and re-raised."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.commit.side_effect = IntegrityError("dup key", {}, None)

        with patch("app.clients.currency.CurrencyClient.validate_currency", return_value=True), \
             patch("app.clients.workspace.WorkspaceClient.create_personal_workspace", return_value=None), \
             patch("app.clients.subscription.SubscriptionClient.set_basic_plan"):
            from app.schemas.user import UserCreate
            service = AuthService(db)
            data = UserCreate(email="dup_integrity@test.com", password="WsPass123!")

            with pytest.raises(UserRegistrationError):
                service.create_user(data)

    def test_unexpected_exception_raises_registration_error(self):
        """Lines 163-166: unexpected DB error is wrapped as UserRegistrationError."""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        db.add.side_effect = RuntimeError("total failure")

        with patch("app.clients.currency.CurrencyClient.validate_currency", return_value=True):
            from app.schemas.user import UserCreate
            service = AuthService(db)
            data = UserCreate(email="unexp_reg@test.com", password="WsPass123!")

            with pytest.raises(UserRegistrationError):
                service.create_user(data)


# ---------------------------------------------------------------------------
# authenticate_user – exception paths
# ---------------------------------------------------------------------------

class TestAuthenticateUserErrorPaths:
    """Lines 207-209: unexpected error raises UserAuthenticationError."""

    def test_unexpected_exception_raises_auth_error(self):
        db = MagicMock()
        db.query.side_effect = RuntimeError("chaos")
        service = AuthService(db)

        from app.schemas.user import UserLogin
        data = UserLogin(email="chaos@test.com", password="ChaosPass1!")

        with pytest.raises(UserAuthenticationError):
            service.authenticate_user(data)


# ---------------------------------------------------------------------------
# create_token – exception path (lines 233-235)
# ---------------------------------------------------------------------------

class TestCreateTokenErrorPath:
    def test_jwt_encode_failure_raises_validation_error(self):
        """Lines 233-235: JWT encode failure raises UserValidationError."""
        db = _make_db()
        service = AuthService(db)
        user = _make_user()

        with patch("jose.jwt.encode", side_effect=Exception("encode failed")):
            with pytest.raises(UserValidationError):
                service.create_token(user)


# ---------------------------------------------------------------------------
# create_refresh_token (lines 239-250)
# ---------------------------------------------------------------------------

class TestCreateRefreshToken:
    def test_creates_refresh_token_successfully(self):
        """create_refresh_token returns a valid JWT."""
        db = _make_db()
        service = AuthService(db)
        user = _make_user()

        token = service.create_refresh_token(user)
        assert isinstance(token, str)

        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["type"] == "refresh"
        assert decoded["sub"] == str(user.id)

    def test_refresh_token_encode_failure_raises_validation_error(self):
        """Lines 248-250: encode failure is wrapped as UserValidationError."""
        db = _make_db()
        service = AuthService(db)
        user = _make_user()

        with patch("jose.jwt.encode", side_effect=Exception("encode failed")):
            with pytest.raises(UserValidationError):
                service.create_refresh_token(user)


# ---------------------------------------------------------------------------
# decode_token – error paths (lines 269-278)
# ---------------------------------------------------------------------------

class TestDecodeTokenErrorPaths:
    def test_user_not_found_after_decode_raises_auth_error(self):
        """Lines 269-275: when user no longer exists, raises UserAuthenticationError."""
        db = _make_db()
        # Provide a valid user initially so token can be created
        user = _make_user(user_id=42)
        db.query.return_value.filter.return_value.first.return_value = user
        service = AuthService(db)
        token = service.create_token(user)

        # Now simulate user deleted from DB
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(UserAuthenticationError):
            service.decode_token(token)

    def test_generic_exception_during_decode_raises_auth_error(self):
        """Lines 276-278: unexpected exception during decode raises UserAuthenticationError."""
        db = MagicMock()
        # Make decode raise an unexpected error
        db.query.side_effect = RuntimeError("db crisis")
        service = AuthService(db)

        # Create a valid token using a clean service
        clean_db = _make_db()
        user = _make_user(user_id=99)
        clean_db.query.return_value.filter.return_value.first.return_value = user
        clean_service = AuthService(clean_db)
        token = clean_service.create_token(user)

        with pytest.raises(UserAuthenticationError):
            service.decode_token(token)


# ---------------------------------------------------------------------------
# refresh_token – error paths (lines 285-296)
# ---------------------------------------------------------------------------

class TestRefreshTokenServiceErrorPaths:
    def test_wrong_token_type_raises_auth_error(self):
        """Lines 285-286: refresh_token rejects non-refresh type tokens."""
        db = _make_db()
        service = AuthService(db)

        # Create an access token (no "type": "refresh")
        user = _make_user(user_id=5)
        db.query.return_value.filter.return_value.first.return_value = user
        access_token = service.create_token(user)

        with pytest.raises(UserAuthenticationError):
            service.refresh_token(access_token)

    def test_invalid_jwt_raises_auth_error(self):
        """Lines 292-293: JWTError is caught and re-raised."""
        db = _make_db()
        service = AuthService(db)

        with pytest.raises(UserAuthenticationError):
            service.refresh_token("garbage.token.data")

    def test_refresh_unexpected_exception_raises_auth_error(self):
        """Lines 294-296: unexpected error during refresh is wrapped."""
        db = MagicMock()
        db.query.side_effect = RuntimeError("db broken")
        service = AuthService(db)

        # Build a valid refresh token
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        payload = {
            "sub": "1",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        with pytest.raises(UserAuthenticationError):
            service.refresh_token(token)


# ---------------------------------------------------------------------------
# change_password – exception paths (lines 328-331)
# ---------------------------------------------------------------------------

class TestChangePasswordErrorPaths:
    def test_unexpected_exception_raises_validation_error(self):
        """Lines 328-331: unexpected error is wrapped as UserValidationError."""
        db = MagicMock()
        user = _make_user(user_id=10)
        db.query.return_value.filter.return_value.first.return_value = user
        db.commit.side_effect = RuntimeError("unexpected db failure")
        service = AuthService(db)

        with pytest.raises(UserValidationError):
            service.change_password(10, "OldPass123!", "NewPass456!")
