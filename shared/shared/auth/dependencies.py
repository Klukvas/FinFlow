"""
Shared FastAPI auth dependencies.

Replaces duplicated get_current_user_id, get_workspace_id, verify_internal_token
across 11 service dependencies.py files.

Config is read from environment variables — no coupling to per-service app.config.
"""

import os
import secrets
from typing import Optional
from uuid import UUID

from fastapi import Depends, Request, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from shared.logging import get_logger, log_security_event

logger = get_logger(__name__)

security = HTTPBearer()


def decode_token(token: str) -> int:
    """Decode JWT token and extract user ID."""
    secret_key = os.environ.get("SECRET_KEY", "")
    algorithm = os.environ.get("ALGORITHM", "HS256")
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        user_id = int(payload["sub"])
        return user_id
    except (JWTError, KeyError, ValueError) as e:
        logger.warning(f"Token decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """Extract and validate user ID from Bearer token."""
    if not credentials or not credentials.credentials:
        log_security_event(logger, "Missing authorization token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required",
        )
    return decode_token(credentials.credentials)


def get_workspace_id(
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
) -> UUID:
    """Extract and validate workspace ID from header."""
    if not x_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Workspace-Id header required",
        )
    try:
        return UUID(x_workspace_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid workspace ID format",
        )


def verify_internal_token(request: Request) -> None:
    """Verify internal service token for inter-service communication."""
    expected_token = os.environ.get("INTERNAL_SECRET_TOKEN", "")
    token = request.headers.get("X-Internal-Token")
    if not token or not expected_token or not secrets.compare_digest(token, expected_token):
        log_security_event(logger, "Invalid or missing internal token", details="Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized internal access",
        )
