from fastapi import APIRouter, Depends, status, Query, Path
from typing import List, Optional
from datetime import datetime, date
from app.schemas.income import IncomeCreate, IncomeOut, IncomeUpdate, IncomeSummary, IncomeStats
from app.services.income import IncomeService
from app.dependencies import get_income_service, get_current_user_id
from app.exceptions import (
    IncomeNotFoundError,
    IncomeValidationError,
    IncomeAmountError,
    IncomeDateError,
    IncomeDescriptionError,
    ExternalServiceError
)

router = APIRouter(prefix="/incomes", tags=["Incomes"])

@router.post(
    "/", 
    response_model=IncomeOut, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new income",
    description="Create a new income with amount, optional category, description and date",
    responses={
        201: {"description": "Income created successfully"},
        400: {"description": "Validation error or category not found"},
        401: {"description": "Unauthorized - invalid or missing token"},
        503: {"description": "External service unavailable"},
    }
)
async def create_income(
    income: IncomeCreate,
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service)
) -> IncomeOut:
    """
    Create a new income.
    
    - **amount**: Income amount (must be greater than 0)
    - **category_id**: Optional category ID for this income
    - **description**: Optional description (max 500 characters)
    - **date**: Optional date (defaults to today if not provided)
    
    Returns the created income with its ID and user association.
    """
    return await service.create(income, user_id)

@router.get(
    "/", 
    response_model=List[IncomeOut],
    summary="Get all incomes",
    description="Retrieve all incomes for the authenticated user, ordered by date (newest first)",
    responses={
        200: {"description": "Incomes retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def get_incomes(
    skip: int = Query(0, ge=0, description="Number of incomes to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of incomes to return"),
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service)
) -> List[IncomeOut]:
    """
    Get all incomes for the authenticated user.
    
    Returns a list of incomes ordered by date (newest first).
    """
    return service.get_all(user_id, skip, limit)

@router.get(
    "/{income_id}",
    response_model=IncomeOut,
    summary="Get income by ID",
    description="Retrieve a specific income by its ID",
    responses={
        200: {"description": "Income retrieved successfully"},
        404: {"description": "Income not found"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def get_income(
    income_id: int = Path(..., gt=0, description="Income ID"),
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service)
) -> IncomeOut:
    """
    Get a specific income by ID.
    
    Returns the income if it exists and belongs to the authenticated user.
    """
    return service.get_by_id(income_id, user_id)

@router.put(
    "/{income_id}",
    response_model=IncomeOut,
    summary="Update income",
    description="Update an existing income",
    responses={
        200: {"description": "Income updated successfully"},
        400: {"description": "Validation error"},
        404: {"description": "Income not found"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
async def update_income(
    income_id: int = Path(..., gt=0, description="Income ID"),
    income_update: IncomeUpdate = ...,
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service)
) -> IncomeOut:
    """
    Update an existing income.
    
    Only provided fields will be updated.
    """
    return await service.update(income_id, income_update, user_id)

@router.delete(
    "/{income_id}",
    summary="Delete income",
    description="Delete an existing income",
    responses={
        200: {"description": "Income deleted successfully"},
        404: {"description": "Income not found"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
async def delete_income(
    income_id: int = Path(..., gt=0, description="Income ID"),
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service)
) -> dict:
    """
    Delete an existing income.
    
    Returns success message if deletion was successful.
    """
    await service.delete(income_id, user_id)
    return {"message": "Income deleted successfully"}

@router.get(
    "/stats/summary",
    response_model=IncomeSummary,
    summary="Get income summary",
    description="Get income summary for a specific date range",
    responses={
        200: {"description": "Income summary retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def get_income_summary(
    start_date: date = Query(..., description="Start date for summary"),
    end_date: date = Query(..., description="End date for summary"),
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service)
) -> IncomeSummary:
    """
    Get income summary for a specific date range.
    
    Returns total income, count, and average for the specified period.
    """
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    return service.get_summary(user_id, start_datetime, end_datetime)

@router.get(
    "/stats/overview",
    response_model=IncomeStats,
    summary="Get income statistics",
    description="Get overall income statistics for the authenticated user",
    responses={
        200: {"description": "Income statistics retrieved successfully"},
        401: {"description": "Unauthorized - invalid or missing token"},
    }
)
def get_income_stats(
    user_id: int = Depends(get_current_user_id),
    service: IncomeService = Depends(get_income_service)
) -> IncomeStats:
    """
    Get overall income statistics.
    
    Returns total, monthly, yearly income and other statistics.
    """
    return service.get_stats(user_id)
