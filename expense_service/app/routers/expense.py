from fastapi import APIRouter, Depends, status, Query, Path
from typing import List, Optional
from datetime import date
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseResponse, ExpenseUpdate, ExpenseSummary, ExpenseStats
from app.services.expense import ExpenseService
from app.dependencies import get_expense_service, get_current_user_id
from app.exceptions import (
    ExpenseNotFoundError,
    ExpenseValidationError,
    ExpenseAmountError,
    ExpenseDateError,
    ExpenseDescriptionError,
    ExternalServiceError
)

router = APIRouter(prefix="/expenses", tags=["Expenses"])

@router.post(
    "/", 
    response_model=ExpenseResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense",
    description="Create a new expense with amount, category, optional description and date",
    responses={
        201: {"description": "Expense created successfully"},
        400: {"description": "Validation error or category not found"},
        401: {"description": "Unauthorized - invalid or missing token"},
        503: {"description": "External service unavailable"},
    }
)
def create_expense(
    expense: ExpenseCreate,
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id)
) -> ExpenseResponse:
    """
    Create a new expense.
    
    - **amount**: Expense amount (must be greater than 0)
    - **category_id**: Category ID for this expense (must exist and belong to user)
    - **description**: Optional description (max 500 characters)
    - **date**: Optional date (defaults to today if not provided)
    
    Returns the created expense with its ID and user association.
    """
    return service.create(expense, user_id)

@router.get(
    "/", 
    response_model=List[ExpenseResponse],
    summary="Get all expenses",
    description="Retrieve all expenses for the authenticated user, ordered by date (newest first)",
    responses={
        200: {"description": "Expenses retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def read_expenses(
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id)
) -> List[ExpenseResponse]:
    """
    Get all expenses for the authenticated user.
    
    Returns a list of all expenses ordered by date (newest first).
    """
    return service.get_all(user_id)

@router.get(
    "/{expense_id}", 
    response_model=ExpenseResponse,
    summary="Get expense by ID",
    description="Retrieve a specific expense by its ID",
    responses={
        200: {"description": "Expense found"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"description": "Expense not found"},
    }
)
def read_expense(
    expense_id: int = Path(description="Expense ID", gt=0),
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id)
) -> ExpenseResponse:
    """
    Get a specific expense by ID.
    
    Returns the expense details if it exists and belongs to the authenticated user.
    """
    return service.get(expense_id, user_id)

@router.patch(
    "/{expense_id}", 
    response_model=ExpenseResponse,
    summary="Update expense",
    description="Update an existing expense's amount, category, description, or date",
    responses={
        200: {"description": "Expense updated successfully"},
        400: {"description": "Validation error or category not found"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"description": "Expense not found"},
        503: {"description": "External service unavailable"},
    }
)
def update_expense(
    expense_id: int = Path(description="Expense ID", gt=0),
    data: ExpenseUpdate = None,
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id)
) -> ExpenseResponse:
    """
    Update an existing expense.
    
    - **amount**: New expense amount (optional)
    - **category_id**: New category ID (optional, must exist and belong to user)
    - **description**: New description (optional, max 500 characters)
    - **date**: New expense date (optional)
    
    Only provided fields will be updated.
    """
    return service.update(expense_id, data, user_id)

@router.delete(
    "/{expense_id}",
    summary="Delete expense",
    description="Delete an expense by its ID",
    responses={
        200: {"description": "Expense deleted successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
        404: {"description": "Expense not found"},
    }
)
def delete_expense(
    expense_id: int = Path(description="Expense ID", gt=0),
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id)
) -> dict:
    """
    Delete an expense.
    
    The expense must belong to the authenticated user.
    """
    return service.delete(expense_id, user_id)

@router.get(
    "/category/{category_id}",
    response_model=List[ExpenseResponse],
    summary="Get expenses by category",
    description="Retrieve all expenses for a specific category",
    responses={
        200: {"description": "Expenses retrieved successfully"},
        400: {"description": "Category not found or doesn't belong to user"},
        401: {"description": "Unauthorized - invalid or missing token"},
        503: {"description": "External service unavailable"},
    }
)
def read_expenses_by_category(
    category_id: int = Path(description="Category ID", gt=0),
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id)
) -> List[ExpenseResponse]:
    """
    Get all expenses for a specific category.
    
    Returns a list of expenses for the specified category, ordered by date (newest first).
    """
    return service.get_by_category(category_id, user_id)

@router.get(
    "/date-range/",
    response_model=List[ExpenseResponse],
    summary="Get expenses by date range",
    description="Retrieve expenses within a specific date range",
    responses={
        200: {"description": "Expenses retrieved successfully"},
        400: {"description": "Invalid date range"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def read_expenses_by_date_range(
    start_date: date = Query(description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(description="End date (YYYY-MM-DD)"),
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id)
) -> List[ExpenseResponse]:
    """
    Get expenses within a date range.
    
    - **start_date**: Start date for the range (inclusive)
    - **end_date**: End date for the range (inclusive)
    
    Returns expenses within the specified date range, ordered by date (newest first).
    """
    return service.get_by_date_range(start_date, end_date, user_id)