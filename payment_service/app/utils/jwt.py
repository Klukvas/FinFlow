from __future__ import annotations

import logging
from typing import Optional
from fastapi import Header, Depends
import jwt

from ..config import settings
from .errors import AuthError

logger = logging.getLogger("payment_service.jwt")


class JWTPayload:
    """JWT token payload"""

    def __init__(self, user_id: str, email: str, workspace_id: Optional[str] = None):
        self.user_id = user_id
        self.email = email
        self.workspace_id = workspace_id


def verify_jwt_token(authorization: str = Header()) -> JWTPayload:
    """
    Verify JWT token from Authorization header
    
    Args:
        authorization: Authorization header value (Bearer <token>)
    
    Returns:
        JWTPayload with user info
    
    Raises:
        AuthError: If token is invalid or missing
    """
    if not authorization:
        raise AuthError(
            "Missing authorization header",
            error_code="@payment_service/MISSING_AUTH_HEADER",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError(
            "Invalid authorization header format",
            error_code="@payment_service/INVALID_AUTH_FORMAT",
        )

    token = parts[1]

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        # Convert user_id to string (it's stored as int in JWT, but we use string/UUID in API)
        user_id = str(payload.get("sub", ""))
        email = payload.get("email", "")
        workspace_id_str = payload.get("workspace_id")
        workspace_id = str(workspace_id_str) if workspace_id_str else None

        return JWTPayload(user_id=user_id, email=email, workspace_id=workspace_id)

    except jwt.ExpiredSignatureError:
        raise AuthError(
            "Token has expired",
            error_code="@payment_service/TOKEN_EXPIRED",
        )
    except jwt.InvalidTokenError as e:
        raise AuthError(
            f"Invalid token: {str(e)}",
            error_code="@payment_service/INVALID_TOKEN",
        )
    except (ValueError, KeyError) as e:
        raise AuthError(
            f"Invalid token payload: {str(e)}",
            error_code="@payment_service/INVALID_TOKEN_PAYLOAD",
        )


def get_current_user(token_payload: JWTPayload = Depends(verify_jwt_token)) -> JWTPayload:
    """Dependency to get current user from JWT token"""
    return token_payload
