from fastapi import APIRouter, Depends, status, Query
from uuid import UUID
from app.dependencies import get_account_service_internal, verify_internal_token
from app.services.account import AccountService
from app.schemas.account import AccountResponse
from app.exceptions import AccountNotFoundError, AccountValidationError, AccountBalanceError

router = APIRouter(prefix="/internal", tags=["internal"])

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
