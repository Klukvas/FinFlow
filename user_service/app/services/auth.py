from passlib.hash import bcrypt
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.exceptions.user_errors import (
    UserServiceError,
    UserErrorCode,
    UserNotFoundError,
    UserValidationError,
    UserAuthenticationError,
    UserRegistrationError,
    PasswordPolicyError,
    UsernamePolicyError,
    AccountLockedError,
    RateLimitError
)
from app.config import settings
from app.utils.logger import get_logger, log_security_event, log_operation, log_authentication_attempt
from app.utils.validation import validate_password_strength, validate_username, validate_email_domain, sanitize_input
from app.utils.rate_limiter import rate_limiter

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        try:
            return self.db.query(User).filter(User.email == email).first()
        except Exception as e:
            self.logger.error(f"Error retrieving user by email: {e}")
            raise UserValidationError("Database error while retrieving user")

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            return self.db.query(User).filter(User.username == username).first()
        except Exception as e:
            self.logger.error(f"Error retrieving user by username: {e}")
            raise UserValidationError("Database error while retrieving user")

    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFoundError(user_id)
            return user
        except UserNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving user by ID: {e}")
            raise UserValidationError("Database error while retrieving user")

    def create_user(self, data: UserCreate) -> User:
        """Create a new user with comprehensive validation and transaction management"""
        try:
            # Sanitize inputs
            email = sanitize_input(data.email.lower().strip())
            username = sanitize_input(data.username.strip())
            password = data.password

            # Validate email domain
            validate_email_domain(email)

            # Validate username
            validate_username(username)

            # Validate password strength
            validate_password_strength(password)

            # Check for existing users
            if self.get_user_by_email(email):
                log_security_event(
                    self.logger,
                    "Registration attempt with existing email",
                    details=f"Email: {email}"
                )
                error = UserRegistrationError(UserServiceError.EMAIL_ALREADY_REGISTERED.value)
                error.error_code = UserErrorCode.EMAIL_ALREADY_TAKEN
                raise error

            if self.get_user_by_username(username):
                log_security_event(
                    self.logger,
                    "Registration attempt with existing username",
                    details=f"Username: {username}"
                )
                error = UserRegistrationError(UserServiceError.USERNAME_ALREADY_REGISTERED.value)
                error.error_code = UserErrorCode.USERNAME_ALREADY_TAKEN
                raise error

            # Hash password
            hashed_password = bcrypt.hash(password)

            # Create user
            user = User(
                email=email,
                username=username,
                hashed_password=hashed_password,
                base_currency=data.base_currency
            )

            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

            log_operation(
                self.logger,
                "User registered",
                user.id,
                f"Email: {email}, Username: {username}"
            )

            return user

        except (UserRegistrationError, PasswordPolicyError, UsernamePolicyError, UserValidationError):
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Database integrity error during user creation: {e}")
            raise UserRegistrationError("User with this email or username already exists")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error during user creation: {e}")
            raise UserRegistrationError("Failed to create user")

    def authenticate_user(self, data: UserLogin) -> User:
        """Authenticate user with rate limiting and account lockout"""
        try:
            # Sanitize email
            email = sanitize_input(data.email.lower().strip())

            # Check rate limiting
            rate_limiter.check_rate_limit(f"login_{email}")

            # Check account lockout
            rate_limiter.check_account_lockout(email)

            # Get user
            user = self.get_user_by_email(email)
            if not user:
                rate_limiter.record_failed_login(email)
                log_authentication_attempt(self.logger, email, False, "User not found")
                raise UserAuthenticationError("Invalid email or password")

            # Verify password
            if not bcrypt.verify(data.password, user.hashed_password):
                rate_limiter.record_failed_login(email)
                log_authentication_attempt(self.logger, email, False, "Invalid password")
                raise UserAuthenticationError("Invalid email or password")

            # Successful authentication
            rate_limiter.record_successful_login(email)
            log_authentication_attempt(self.logger, email, True)
            log_operation(
                self.logger,
                "User authenticated",
                user.id,
                f"Email: {email}"
            )

            return user

        except (UserAuthenticationError, AccountLockedError, RateLimitError):
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {e}")
            raise UserAuthenticationError("Authentication failed")

    def create_token(self, user: User) -> str:
        """Create JWT access token"""
        try:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            payload = {
                "sub": str(user.id),
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "email": user.email,
                "username": user.username
            }
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            
            log_operation(
                self.logger,
                "Token created",
                user.id,
                f"Expires: {expire}"
            )
            
            return token
        except Exception as e:
            self.logger.error(f"Error creating token: {e}")
            raise UserValidationError("Failed to create authentication token")

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        try:
            expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            payload = {
                "sub": str(user.id),
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "refresh"
            }
            return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        except Exception as e:
            self.logger.error(f"Error creating refresh token: {e}")
            raise UserValidationError("Failed to create refresh token")

    def decode_token(self, token: str) -> int:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = int(payload["sub"])
            
            # Verify user still exists
            self.get_user_by_id(user_id)
            
            return user_id
        except JWTError as e:
            log_security_event(
                self.logger,
                "Invalid token provided",
                details=f"Error: {e}"
            )
            raise UserAuthenticationError("Invalid or expired token")
        except UserNotFoundError:
            log_security_event(
                self.logger,
                "Token for non-existent user",
                details=f"User ID: {payload.get('sub', 'unknown')}"
            )
            raise UserAuthenticationError("Invalid token")
        except Exception as e:
            self.logger.error(f"Error decoding token: {e}")
            raise UserAuthenticationError("Token validation failed")

    def refresh_token(self, refresh_token: str) -> str:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            if payload.get("type") != "refresh":
                raise UserAuthenticationError("Invalid refresh token")
            
            user_id = int(payload["sub"])
            user = self.get_user_by_id(user_id)
            
            return self.create_token(user)
        except JWTError:
            raise UserAuthenticationError("Invalid refresh token")
        except Exception as e:
            self.logger.error(f"Error refreshing token: {e}")
            raise UserAuthenticationError("Token refresh failed")

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        """Change user password with validation"""
        try:
            user = self.get_user_by_id(user_id)
            
            # Verify old password
            if not bcrypt.verify(old_password, user.hashed_password):
                log_security_event(
                    self.logger,
                    "Password change with invalid old password",
                    user_id
                )
                raise UserAuthenticationError("Current password is incorrect")
            
            # Validate new password
            validate_password_strength(new_password)
            
            # Hash new password
            user.hashed_password = bcrypt.hash(new_password)
            self.db.commit()
            
            log_operation(
                self.logger,
                "Password changed",
                user_id
            )
            
        except (UserAuthenticationError, PasswordPolicyError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error changing password: {e}")
            raise UserValidationError("Failed to change password")