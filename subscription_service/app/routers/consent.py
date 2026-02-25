"""
Consent API endpoints for recording and retrieving user consent
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.consent import ConsentService
from ..schemas.consent import (
    ConsentRecordRequest,
    ConsentRecordResponse,
    ConsentHistoryResponse,
    ConsentVersionResponse,
)

router = APIRouter(prefix="/consent", tags=["consent"])


@router.post("/{user_id}/record", response_model=ConsentRecordResponse)
def record_consent(
    user_id: str,
    request_data: ConsentRecordRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """
    Record user consent for subscription.
    
    This creates an immutable audit log entry with the full consent text,
    timestamp, IP address, and user agent. Required for payment provider compliance.
    
    This endpoint is typically called internally by the payment service
    after a successful initial subscription payment.
    
    **Compliance Note:** The consent record is immutable and can be used to
    prove compliance in case of disputes or audits.
    """
    service = ConsentService(db)
    
    # Extract request metadata
    ip_address = http_request.client.host if http_request.client else "unknown"
    user_agent = http_request.headers.get("user-agent", "")
    
    consent_log = service.record_consent(
        subscription_id=request_data.subscription_id,
        user_id=user_id,
        consent_version=request_data.consent_version,
        consent_language=request_data.consent_language,
        plan_name=request_data.plan_name,
        plan_code=request_data.plan_code,
        amount=request_data.amount,
        currency=request_data.currency,
        ip_address=ip_address,
        user_agent=user_agent,
        browser_fingerprint=request_data.browser_fingerprint,
    )
    
    return ConsentRecordResponse.model_validate(consent_log)


@router.get("/{user_id}/history", response_model=list[ConsentHistoryResponse])
def get_consent_history(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Get consent history for a user.
    
    Returns all consent events for the user, ordered by most recent first.
    Useful for:
    - User data export requests (GDPR)
    - Showing user their consent history
    - Compliance audits
    """
    service = ConsentService(db)
    consent_logs = service.get_user_consent_history(user_id)
    
    return [ConsentHistoryResponse.model_validate(log) for log in consent_logs]


@router.get("/current-version", response_model=ConsentVersionResponse)
def get_current_consent_version():
    """
    Get the current consent version and supported languages.
    
    Frontend should call this to ensure they're using the correct consent version.
    If the version changes, users will need to re-consent.
    """
    return ConsentVersionResponse(
        version=ConsentService.get_current_consent_version(),
        supported_languages=ConsentService.get_supported_languages(),
    )
