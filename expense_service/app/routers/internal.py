from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Annotated

from app.schemas.expense import ExpenseCreate, ExpenseResponse
from app.services.expense import ExpenseService
from app.dependencies import get_expense_service_internal, verify_internal_token
from app.utils.logger import get_logger

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating expense"
        )