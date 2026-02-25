"""Shared authentication utilities for subscription_service."""
from __future__ import annotations

import secrets

from fastapi import Header

from ..config import settings
from ..utils.errors import AuthError


def verify_internal_token(internal_token: str = Header(alias="X-Internal-Token")) -> None:
    """Verify internal service token for service-to-service calls."""
    if not settings.internal_secret_token:
        raise AuthError(
            "Internal secret token not configured",
            error_code="@subscription_service/TOKEN_NOT_CONFIGURED",
        )
    if not secrets.compare_digest(internal_token, settings.internal_secret_token):
        raise AuthError(
            "Invalid internal token",
            error_code="@subscription_service/INVALID_INTERNAL_TOKEN",
        )
