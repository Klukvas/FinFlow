from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.dependencies import get_account_service_internal, verify_internal_token
from app.services.account import AccountService
from app.schemas.account import AccountResponse

router = APIRouter(prefix="/internal", tags=["internal"])

@router.get("/accounts/{account_id}/validate")
async def validate_account(
    account_id: int,
    user_id: int = Query(..., description="User ID to validate ownership"),
    _: None = Depends(verify_internal_token),
    service: AccountService = Depends(get_account_service_internal)
) -> dict:
    """Validate that an account exists and belongs to the specified user"""
    try:
        is_valid = service.validate_account_ownership(account_id, user_id)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or not owned by user"
            )
        
        # Get account details
        account = service.get_account(account_id, user_id)
        
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
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account validation failed: {str(e)}"
        )

@router.get("/accounts/{account_id}")
async def get_account_internal(
    account_id: int,
    user_id: int = Query(..., description="User ID to validate ownership"),
    _: None = Depends(verify_internal_token),
    service: AccountService = Depends(get_account_service_internal)
) -> AccountResponse:
    """Get account details for internal service use"""
    try:
        account = service.get_account(account_id, user_id)
        return AccountResponse.model_validate(account)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account not found: {str(e)}"
        )

@router.put("/accounts/{account_id}/balance")
async def update_account_balance_internal(
    account_id: int,
    user_id: int = Query(..., description="User ID to validate ownership"),
    amount_change: float = Query(..., description="Amount to add (positive) or subtract (negative)"),
    transaction_currency: str = Query("USD", description="Currency of the transaction"),
    _: None = Depends(verify_internal_token),
    service: AccountService = Depends(get_account_service_internal)
) -> AccountResponse:
    """Update account balance by adding/subtracting an amount with automatic currency conversion"""
    try:
        # Update balance with currency conversion
        updated_account = await service.update_balance_with_conversion(
            account_id, amount_change, transaction_currency, user_id
        )
        
        return AccountResponse.model_validate(updated_account)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update account balance: {str(e)}"
        )
