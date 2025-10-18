from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Annotated, List

from app.schemas.expense import ExpenseCreate, ExpenseResponse
from app.services.expense import ExpenseService
from app.dependencies import get_expense_service_internal, verify_internal_token
from app.utils.logger import get_logger
from app.models.expense import Expense
from app.exceptions import ErrorCode, ExpenseValidationError

# Create a separate router for internal endpoints
router = APIRouter(prefix="/internal", tags=["Internal"])
logger = get_logger(__name__)


@router.post(
    '/',
    response_model=ExpenseResponse,
    summary="Create expense for internal use",
    description="Internal endpoint for other services to create expenses",
    responses={
        200: {"description": "Expense created successfully"},
        403: {"description": "Invalid internal token or unauthorized access"},
        400: {"description": "Invalid expense data"},
    }
)
async def internal_expense_create(
    expense: ExpenseCreate,
    user_id: Annotated[int, Query(description="User ID to validate ownership", gt=0)],
    service: ExpenseService = Depends(get_expense_service_internal),
    _: None = Depends(verify_internal_token)
) -> ExpenseResponse:
    """
    Internal endpoint for other services to create expenses.
    
    This endpoint is used by other microservices to:
    - Create expenses on behalf of users
    - Validate expense data
    - Handle internal expense creation logic
    
    Args:
        expense: The expense data to create
        user_id: The ID of the user who owns the expense
        service: Injected expense service instance
        
    Returns:
        ExpenseResponse: The created expense details
        
    Raises:
        HTTPException: 403 if invalid internal token or unauthorized access
        HTTPException: 400 if invalid expense data
    """
    try:
        created_expense = service.create(expense, user_id)
        
        logger.info(f"Internal expense created: {created_expense.id} for user {user_id}")
        
        return created_expense
        
    except Exception as e:
        logger.error(f"Unexpected error in internal expense creation: {e}")
        raise ExpenseValidationError(
            "Internal server error while creating expense",
            ErrorCode.EXPENSE_CREATION_FAILED,
            {"original_error": str(e)}
        )


@router.get(
    '/expenses/account/{account_id}',
    response_model=List[ExpenseResponse],
    summary="Get expenses by account",
    description="Internal endpoint to get expenses for a specific account",
    responses={
        200: {"description": "Expenses retrieved successfully"},
        403: {"description": "Invalid internal token"},
        404: {"description": "Account not found"},
    }
)
async def get_expenses_by_account(
    account_id: int,
    user_id: Annotated[int, Query(description="User ID to validate ownership", gt=0)],
    limit: Annotated[int, Query(description="Maximum number of expenses to return", ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(description="Number of expenses to skip", ge=0)] = 0,
    service: ExpenseService = Depends(get_expense_service_internal),
    _: None = Depends(verify_internal_token)
) -> List[ExpenseResponse]:
    """
    Internal endpoint to get expenses for a specific account.
    
    This endpoint is used by the account service to:
    - Fetch expenses associated with a specific account
    - Validate account ownership
    - Support account transaction summaries
    
    Args:
        account_id: The ID of the account
        user_id: The ID of the user who owns the account
        limit: Maximum number of expenses to return
        offset: Number of expenses to skip
        service: Injected expense service instance
        
    Returns:
        List[ExpenseResponse]: List of expenses for the account
        
    Raises:
        HTTPException: 403 if invalid internal token
        HTTPException: 404 if account not found
    """
    try:
        # Get expenses for the account
        expenses = service.db.query(Expense).filter(
            Expense.account_id == account_id,
            Expense.user_id == user_id
        ).order_by(Expense.date.desc()).offset(offset).limit(limit).all()
        
        logger.info(f"Retrieved {len(expenses)} expenses for account {account_id} and user {user_id}")
        
        return expenses
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving expenses by account: {e}")
        raise ExpenseValidationError(
            "Internal server error while retrieving expenses",
            ErrorCode.EXPENSE_RETRIEVAL_FAILED,
            {"original_error": str(e), "account_id": account_id}
        )


@router.get(
    '/expenses/account/{account_id}/validate',
    summary="Validate account for expenses",
    description="Internal endpoint to validate that an account can be used for expenses",
    responses={
        200: {"description": "Account is valid for expenses"},
        403: {"description": "Invalid internal token"},
        404: {"description": "Account not found or not owned by user"},
    }
)
async def validate_account_for_expenses(
    account_id: int,
    user_id: Annotated[int, Query(description="User ID to validate ownership", gt=0)],
    service: ExpenseService = Depends(get_expense_service_internal),
    _: None = Depends(verify_internal_token)
) -> dict:
    """
    Internal endpoint to validate that an account can be used for expenses.
    
    This endpoint is used by the account service to:
    - Validate account ownership
    - Check if account is active and not archived
    - Ensure account can be used for expense transactions
    
    Args:
        account_id: The ID of the account to validate
        user_id: The ID of the user who should own the account
        service: Injected expense service instance
        
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
        raise ExpenseValidationError(
            "Account not found or not owned by user",
            ErrorCode.ACCOUNT_NOT_FOUND,
            {"original_error": str(e), "account_id": account_id, "user_id": user_id}
        )