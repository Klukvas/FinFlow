from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.subscriptions import SubscriptionService
from ..repositories.subscriptions import SubscriptionRepository
from ..schemas.subscription import SetPlanIn, SubscriptionOut
from ..schemas.cancellation import CancelSubscriptionRequest, CancelSubscriptionResponse
from ..utils.errors import ConflictError, NotFoundError
from ..utils.idempotency import IdempotencyStore
from ..utils.auth import verify_internal_token


router = APIRouter()

_IDEMPOTENCY_KEYS: dict[str, str] = {}


@router.get("/subscriptions/{user_id}", response_model=SubscriptionOut | None)
def get_subscription(user_id: str, db: Session = Depends(get_db)):
    """Get user's current subscription. Returns null if no active subscription."""
    repo = SubscriptionRepository(db)
    subscription = repo.get_active_subscription(user_id)

    if subscription is None:
        return None

    return SubscriptionOut.model_validate(subscription, from_attributes=True)


@router.post("/subscriptions/{user_id}:set_plan")
def set_plan(
    user_id: str,
    payload: SetPlanIn,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if idempotency_key:
        store = IdempotencyStore()
        ok = store.check_and_set(idempotency_key, f"{user_id}:{payload.plan_code}")
        if not ok:
            raise ConflictError("Idempotency-Key conflict", error_code="@subscription_service/IDEMPOTENCY_VIOLATION")

    service = SubscriptionService(db)
    result = service.set_plan(user_id, payload.plan_code, payload.status)
    sub = result["subscription"]
    response = SubscriptionOut.model_validate(sub, from_attributes=True).model_dump(mode="json")

    if result["is_downgrade"]:
        response["downgrade_impact"] = result["downgrade_impact"]
        response["is_downgrade"] = True

    return response


@router.delete("/subscriptions/{user_id}/cancel", response_model=CancelSubscriptionResponse)
def cancel_subscription(
    user_id: str,
    request_data: CancelSubscriptionRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Cancel the current user's subscription.
    
    **CRITICAL FOR COMPLIANCE:** This endpoint allows users to cancel their
    subscription without contacting support, as required by Paddle and
    consumer protection laws.
    
    **Two Cancellation Options:**
    
    1. **Cancel at Period End** (Recommended, `cancel_immediately=false`):
       - User keeps access until the end of the current billing period
       - No refund needed
       - Better user experience
       - Sets `auto_renew=false` to prevent future charges
    
    2. **Cancel Immediately** (`cancel_immediately=true`):
       - User loses access immediately
       - May issue pro-rata refund (business decision)
       - Sets `auto_renew=false` and `status=canceled`
    
    **What Happens:**
    - `auto_renew` is set to `false` (prevents future charges)
    - Cancellation timestamp, reason, and IP are logged for audit trail
    - Confirmation email is sent (TODO)
    - User can reactivate anytime before period ends
    """
    service = SubscriptionService(db)
    
    # Extract IP address for audit trail
    ip_address = http_request.client.host if http_request.client else "unknown"
    
    subscription = service.cancel_subscription(
        user_id=user_id,
        cancellation_reason=request_data.cancellation_reason,
        cancellation_comment=request_data.cancellation_comment,
        cancel_immediately=request_data.cancel_immediately,
        ip_address=ip_address,
    )
    
    # Determine when access ends
    access_ends_at = subscription.expires_at
    
    # Create user-friendly message
    if request_data.cancel_immediately:
        message = "Subscription canceled immediately. Access has been revoked."
    else:
        if access_ends_at:
            message = f"Subscription canceled. You'll have access until {access_ends_at.strftime('%B %d, %Y')}."
        else:
            message = "Subscription canceled. No future charges will be made."
    
    return CancelSubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        plan_code=subscription.plan_code,
        status=subscription.status,
        auto_renew=subscription.auto_renew,
        canceled_at=subscription.canceled_at,
        expires_at=subscription.expires_at,
        cancellation_reason=subscription.cancellation_reason,
        access_ends_at=access_ends_at,
        message=message,
    )


# Keep legacy endpoint for backwards compatibility
@router.post("/subscriptions/{user_id}:cancel", response_model=SubscriptionOut, deprecated=True)
def cancel_subscription_legacy(user_id: str, http_request: Request, db: Session = Depends(get_db)):
    """
    Legacy cancellation endpoint (deprecated).
    
    Use DELETE /subscriptions/my-subscription instead.
    """
    service = SubscriptionService(db)
    ip_address = http_request.client.host if http_request.client else "unknown"
    
    subscription = service.cancel_subscription(
        user_id=user_id,
        cancellation_reason=None,
        cancellation_comment=None,
        cancel_immediately=False,
        ip_address=ip_address,
    )
    
    return SubscriptionOut.model_validate(subscription, from_attributes=True)


