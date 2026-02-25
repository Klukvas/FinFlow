"""Admin authorization guard for payment service"""
from __future__ import annotations

import logging
from fastapi import HTTPException, Request, status
import jwt

from ..config import settings

logger = logging.getLogger("payment_service")


def verify_admin_token(request: Request) -> dict:
    """
    Verify JWT and check admin role.
    Returns the decoded token payload if valid admin.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )

    token = auth_header.split(" ")[1]

    if not settings.jwt_secret_key:
        logger.error("JWT secret key not configured in payment service")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service configuration error",
        )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_role = payload.get("role")
        if user_role != "admin":
            logger.warning(
                f"Admin access denied for user {payload.get('sub')} with role {user_role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
