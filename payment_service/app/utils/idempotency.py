from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Any
from fastapi import Header, Request
from sqlalchemy.orm import Session

from ..models.models import IdempotencyKey
from ..config import settings
from .errors import ConflictError

logger = logging.getLogger("payment_service.idempotency")


def compute_request_hash(body: dict[str, Any]) -> str:
    """Compute hash of request body for idempotency check"""
    body_str = json.dumps(body, sort_keys=True)
    return hashlib.sha256(body_str.encode()).hexdigest()


def check_idempotency(
    db: Session,
    idempotency_key: str,
    scope: str,
    request_hash: str,
) -> Optional[dict[str, Any]]:
    """
    Check if request with this idempotency key was already processed
    
    Args:
        db: Database session
        idempotency_key: Idempotency key from header
        scope: Scope/endpoint identifier
        request_hash: Hash of request body
    
    Returns:
        Previous response if key exists, None otherwise
    
    Raises:
        ConflictError: If key exists with different request body
    """
    existing = db.query(IdempotencyKey).filter(
        IdempotencyKey.key == idempotency_key,
        IdempotencyKey.scope == scope,
        IdempotencyKey.expires_at > datetime.utcnow(),
    ).first()

    if not existing:
        return None

    # Same key with different request body - conflict
    if existing.request_hash != request_hash:
        raise ConflictError(
            "Idempotency key conflict: same key with different request body",
            error_code="@payment_service/IDEMPOTENCY_CONFLICT",
            details={
                "idempotency_key": idempotency_key,
                "scope": scope,
            },
        )

    # Return cached response
    logger.info(
        f"Idempotency key hit: {idempotency_key}",
        extra={
            "idempotency_key": idempotency_key,
            "scope": scope,
        },
    )

    return existing.response_body


def store_idempotency(
    db: Session,
    idempotency_key: str,
    scope: str,
    request_hash: str,
    response_body: dict[str, Any],
    response_status: str,
):
    """
    Store idempotency key with response for future duplicate requests
    
    Args:
        db: Database session
        idempotency_key: Idempotency key
        scope: Scope/endpoint identifier
        request_hash: Hash of request body
        response_body: Response to cache
        response_status: Response status code
    """
    expires_at = datetime.utcnow() + timedelta(seconds=settings.idempotency_ttl_seconds)

    key_record = IdempotencyKey(
        key=idempotency_key,
        scope=scope,
        request_hash=request_hash,
        response_body=response_body,
        response_status=response_status,
        expires_at=expires_at,
    )

    db.add(key_record)
    db.commit()

    logger.info(
        f"Stored idempotency key: {idempotency_key}",
        extra={
            "idempotency_key": idempotency_key,
            "scope": scope,
            "expires_at": expires_at.isoformat(),
        },
    )


async def get_idempotency_key(
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> Optional[str]:
    """Dependency to extract idempotency key from header"""
    return idempotency_key
