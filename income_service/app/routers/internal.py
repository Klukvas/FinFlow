from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Annotated, List

from app.schemas.income import IncomeCreate, IncomeOut
from app.services.income import IncomeService
from app.dependencies import get_income_service
from app.utils.logger import get_logger
from app.models.income import Income

# Create a separate router for internal endpoints
router = APIRouter(prefix="/internal", tags=["Internal"])
logger = get_logger(__name__)

def verify_internal_token(request) -> None:
    """Verify internal service token for inter-service communication"""
    token = request.headers.get("X-Internal-Token")
    if not token:
        logger.warning("Missing internal token")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internal token required"
        )
    
    # In a real implementation, you would validate the token
    # For now, we'll just check if it exists
    if token != "my-secret-token":
        logger.warning("Invalid internal token")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized internal access"
        )

@router.get(
    '/incomes/account/{account_id}',
    response_model=List[IncomeOut],
    summary="Get incomes by account",
    description="Internal endpoint to get incomes for a specific account",
    responses={
        200: {"description": "Incomes retrieved successfully"},
        403: {"description": "Invalid internal token"},
        404: {"description": "Account not found"},
    }
)
async def get_incomes_by_account(
    account_id: int,
    user_id: Annotated[int, Query(description="User ID to validate ownership", gt=0)],
    limit: Annotated[int, Query(description="Maximum number of incomes to return", ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(description="Number of incomes to skip", ge=0)] = 0,
    service: IncomeService = Depends(get_income_service),
    _: None = Depends(verify_internal_token)
) -> List[IncomeOut]:
    """
    Internal endpoint to get incomes for a specific account.
    
    This endpoint is used by the account service to:
    - Fetch incomes associated with a specific account
    - Validate account ownership
    - Support account transaction summaries
    
    Args:
        account_id: The ID of the account
        user_id: The ID of the user who owns the account
        limit: Maximum number of incomes to return
        offset: Number of incomes to skip
        service: Injected income service instance
        
    Returns:
        List[IncomeOut]: List of incomes for the account
        
    Raises:
        HTTPException: 403 if invalid internal token
        HTTPException: 404 if account not found
    """
    try:
        # Get incomes for the account
        incomes = service.db.query(Income).filter(
            Income.account_id == account_id,
            Income.user_id == user_id
        ).order_by(Income.date.desc()).offset(offset).limit(limit).all()
        
        logger.info(f"Retrieved {len(incomes)} incomes for account {account_id} and user {user_id}")
        
        return [IncomeOut.from_orm(income) for income in incomes]
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving incomes by account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving incomes"
        )


@router.get(
    '/incomes/account/{account_id}/validate',
    summary="Validate account for incomes",
    description="Internal endpoint to validate that an account can be used for incomes",
    responses={
        200: {"description": "Account is valid for incomes"},
        403: {"description": "Invalid internal token"},
        404: {"description": "Account not found or not owned by user"},
    }
)
async def validate_account_for_incomes(
    account_id: int,
    user_id: Annotated[int, Query(description="User ID to validate ownership", gt=0)],
    service: IncomeService = Depends(get_income_service),
    _: None = Depends(verify_internal_token)
) -> dict:
    """
    Internal endpoint to validate that an account can be used for incomes.
    
    This endpoint is used by the account service to:
    - Validate account ownership
    - Check if account is active and not archived
    - Ensure account can be used for income transactions
    
    Args:
        account_id: The ID of the account to validate
        user_id: The ID of the user who should own the account
        service: Injected income service instance
        
    Returns:
        dict: Validation result with account details
        
    Raises:
        HTTPException: 403 if invalid internal token
        HTTPException: 404 if account not found or not owned by user
    """
    try:
        # Validate account through the account service client
        account_data = service.account_client.validate_account(account_id, user_id)
        
        logger.info(f"Account {account_id} validated successfully for user {user_id}")
        
        return {
            "valid": True,
            "account_id": account_id,
            "user_id": user_id,
            "account": account_data.get("account", {})
        }
        
    except Exception as e:
        logger.error(f"Account validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or not owned by user"
        )
