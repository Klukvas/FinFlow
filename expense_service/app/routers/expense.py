from fastapi import APIRouter, Depends, status, Query, Path
from typing import List, Optional, Annotated
from datetime import date
from uuid import UUID
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate, ExpenseSummary, ExpenseStats, ExpenseListResponse, ExpensesByCategoryResponse
from app.services.expense import ExpenseService
from app.dependencies import get_expense_service, get_current_user_id, get_workspace_id
from app.exceptions import (
    ErrorCode,
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
        403: {"description": "Forbidden - insufficient workspace permissions"},
        503: {"description": "External service unavailable"},
    }
)
def create_expense(
    expense: ExpenseCreate,
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> ExpenseResponse:
    """
    Create a new expense.
    
    - **amount**: Expense amount (must be greater than 0)
    - **category_id**: Category ID for this expense (must exist and belong to user)
    - **description**: Optional description (max 500 characters)
    - **date**: Optional date (defaults to today if not provided)
    
    Requires 'member' role in the workspace.
    Returns the created expense with its ID and user association.
    """
    return service.create(expense, user_id, workspace_id)

@router.get(
    "/", 
    response_model=List[ExpenseResponse],
    summary="Get all expenses",
    description="Retrieve all expenses in the workspace, ordered by date (newest first)",
    responses={
        200: {"description": "Expenses retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
        403: {"description": "Forbidden - insufficient workspace permissions"},
    }
)
def read_expenses(
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> List[ExpenseResponse]:
    """
    Get all expenses in the workspace.
    
    Requires 'viewer' role in the workspace.
    Returns a list of all expenses ordered by date (newest first).
    """
    return service.get_all(user_id, workspace_id)

@router.get(
    "/paginated", 
    response_model=ExpenseListResponse,
    summary="Get paginated expenses",
    description="Retrieve paginated expenses in the workspace with pagination metadata",
    responses={
        200: {"description": "Expenses retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
        403: {"description": "Forbidden - insufficient workspace permissions"},
    }
)
def read_expenses_paginated(
    page: Annotated[int, Query(description="Page number", ge=1)] = 1,
    size: Annotated[int, Query(description="Number of items per page", ge=1, le=100)] = 50,
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> ExpenseListResponse:
    """
    Get paginated expenses in the workspace.
    
    - **page**: Page number (starts from 1)
    - **size**: Number of items per page (1-100, default 50)
    
    Requires 'viewer' role in the workspace.
    Returns paginated results with metadata including total count, current page, and total pages.
    """
    expenses, total = service.get_all_paginated(user_id, workspace_id, page, size)
    
    pages = (total + size - 1) // size  # Calculate total pages
    
    return ExpenseListResponse(
        items=expenses,
        total=total,
        page=page,
        size=size,
        pages=pages
    )

@router.get(
    "/current-month-count",
    summary="Get current month expense count",
    description="Get the number of expenses created this month and the monthly limit",
    responses={
        200: {"description": "Current month count and limit returned successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def get_current_month_count(
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
):
    """
    Get current month expense count and limit.

    Returns:
        - count: Number of expenses created this month
        - limit: Monthly limit for this user's plan (None = unlimited)
    """
    return service.get_current_month_count(user_id, workspace_id)

@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get expense by ID",
    description="Retrieve a specific expense by its ID",
    responses={
        200: {"description": "Expense found"},
        401: {"description": "Unauthorized - invalid or missing token"},
        403: {"description": "Forbidden - insufficient workspace permissions"},
        404: {"description": "Expense not found"},
    }
)
def read_expense(
    expense_id: int = Path(description="Expense ID", gt=0),
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> ExpenseResponse:
    """
    Get a specific expense by ID.
    
    Requires 'viewer' role in the workspace.
    Returns the expense details if it exists and belongs to the workspace.
    """
    return service.get(expense_id, user_id, workspace_id)

@router.patch(
    "/{expense_id}", 
    response_model=ExpenseResponse,
    summary="Update expense",
    description="Update an existing expense's amount, category, description, or date",
    responses={
        200: {"description": "Expense updated successfully"},
        400: {"description": "Validation error or category not found"},
        401: {"description": "Unauthorized - invalid or missing token"},
        403: {"description": "Forbidden - insufficient workspace permissions"},
        404: {"description": "Expense not found"},
        503: {"description": "External service unavailable"},
    }
)
def update_expense(
    data: ExpenseUpdate,
    expense_id: int = Path(description="Expense ID", gt=0),
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> ExpenseResponse:
    """
    Update an existing expense.
    
    - **amount**: New expense amount (optional)
    - **category_id**: New category ID (optional, must exist and belong to user)
    - **description**: New description (optional, max 500 characters)
    - **date**: New expense date (optional)
    
    Requires 'member' role in the workspace.
    Only provided fields will be updated.
    """
    return service.update(expense_id, data, user_id, workspace_id)

@router.delete(
    "/{expense_id}",
    status_code=204,
    summary="Delete expense",
    description="Delete an expense by its ID",
    responses={
        204: {"description": "Expense deleted successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
        403: {"description": "Forbidden - insufficient workspace permissions"},
        404: {"description": "Expense not found"},
    }
)
def delete_expense(
    expense_id: int = Path(description="Expense ID", gt=0),
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
):
    """
    Delete an expense.

    Requires 'member' role in the workspace.
    The expense must belong to the workspace.
    """
    service.delete(expense_id, user_id, workspace_id)

@router.get(
    "/category/{category_id}",
    response_model=ExpensesByCategoryResponse,
    summary="Get expenses by category",
    description="Retrieve all expenses for a specific category with statistics",
    responses={
        200: {"description": "Expenses retrieved successfully"},
        400: {"description": "Category not found or doesn't belong to user"},
        401: {"description": "Unauthorized - invalid or missing token"},
        403: {"description": "Forbidden - insufficient workspace permissions"},
        503: {"description": "External service unavailable"},
    }
)
def read_expenses_by_category(
    category_id: int = Path(description="Category ID", gt=0),
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> ExpensesByCategoryResponse:
    """
    Get all expenses for a specific category with statistics in the workspace.
    
    Requires 'viewer' role in the workspace.
    Returns a list of expenses for the specified category (ordered by date, newest first) along with
    statistics including total amount, count, and average amount, all converted to the user's base currency.
    """
    return service.get_by_category(category_id, user_id, workspace_id)

@router.get(
    "/date-range/",
    response_model=List[ExpenseResponse],
    summary="Get expenses by date range",
    description="Retrieve expenses within a specific date range",
    responses={
        200: {"description": "Expenses retrieved successfully"},
        400: {"description": "Invalid date range"},
        401: {"description": "Unauthorized - invalid or missing token"},
        403: {"description": "Forbidden - insufficient workspace permissions"},
    }
)
def read_expenses_by_date_range(
    start_date: date = Query(description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(description="End date (YYYY-MM-DD)"),
    service: ExpenseService = Depends(get_expense_service),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id)
) -> List[ExpenseResponse]:
    """
    Get expenses within a date range in the workspace.
    
    - **start_date**: Start date for the range (inclusive)
    - **end_date**: End date for the range (inclusive)
    
    Requires 'viewer' role in the workspace.
    Returns expenses within the specified date range, ordered by date (newest first).
    """
    return service.get_by_date_range(start_date, end_date, user_id, workspace_id)