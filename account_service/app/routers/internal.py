import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated
from uuid import UUID
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_account_service_internal, verify_internal_token
from app.services.account import AccountService
from app.schemas.account import AccountResponse
from app.models.account import Account
from app.exceptions import AccountNotFoundError, AccountValidationError, AccountBalanceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get(
    "/accounts/ai-summary",
    summary="Get accounts summary for AI analysis",
    description="Internal endpoint returning aggregated account data for AI assistant analysis",
    responses={
        200: {"description": "Accounts summary retrieved successfully"},
        403: {"description": "Invalid internal token"},
    }
)
async def get_accounts_ai_summary(
    user_id: Annotated[int, Query(description="User ID", gt=0)],
    workspace_id: Annotated[UUID, Query(description="Workspace ID")],
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token),
) -> dict:
    """
    Internal endpoint returning all active accounts for AI analysis.

    Returns aggregated data without PII for the AI assistant to analyze
    account balances and provide financial insights.
    """
    try:
        accounts = (
            db.query(Account)
            .filter(
                Account.owner_id == user_id,
                Account.workspace_id == workspace_id,
                Account.is_active.is_(True),
            )
            .limit(200)
            .all()
        )
        return {
            "items": [
                {
                    "name": a.name,
                    "type": str(a.type.value) if a.type else None,
                    "balance": float(a.balance),
                    "currency": a.currency,
                }
                for a in accounts
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching accounts AI summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve accounts summary",
        )


@router.get("/accounts/{account_id}/validate")
def validate_account(
    account_id: int,
    user_id: int = Query(..., description="User ID to validate ownership"),
    workspace_id: UUID = Query(..., description="Workspace ID for isolation"),
    _: None = Depends(verify_internal_token),
    service: AccountService = Depends(get_account_service_internal)
) -> dict:
    """Validate that an account exists and belongs to the specified user"""
    account = service.get_account(account_id, user_id, workspace_id)

    return {
        "valid": True,
        "account": {
            "id": account.id,
            "name": account.name,
            "type": account.type.value,
            "currency": account.currency,
            "balance": account.balance,
            "is_active": account.is_active,
            "is_archived": account.is_archived
        }
    }

@router.get("/accounts/{account_id}")
def get_account_internal(
    account_id: int,
    user_id: int = Query(..., description="User ID to validate ownership"),
    workspace_id: UUID = Query(..., description="Workspace ID for isolation"),
    _: None = Depends(verify_internal_token),
    service: AccountService = Depends(get_account_service_internal)
) -> AccountResponse:
    """Get account details for internal service use"""
    account = service.get_account(account_id, user_id, workspace_id)
    return AccountResponse.model_validate(account)

@router.put("/accounts/{account_id}/balance")
async def update_account_balance_internal(
    account_id: int,
    user_id: int = Query(..., description="User ID to validate ownership"),
    workspace_id: UUID = Query(..., description="Workspace ID for isolation"),
    amount_change: float = Query(..., description="Amount to add (positive) or subtract (negative)"),
    transaction_currency: str = Query("USD", description="Currency of the transaction"),
    _: None = Depends(verify_internal_token),
    service: AccountService = Depends(get_account_service_internal)
) -> AccountResponse:
    """Update account balance by adding/subtracting an amount with automatic currency conversion"""
    updated_account = await service.update_balance_with_conversion(
        account_id, amount_change, transaction_currency, user_id, workspace_id
    )

    return AccountResponse.model_validate(updated_account)
