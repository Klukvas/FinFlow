
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_debt_service, get_current_user_id
from app.services.debt import DebtService
from app.schemas.debt import (
    DebtCreate, DebtUpdate, DebtResponse, DebtSummary,
    DebtPaymentCreate, DebtPaymentResponse
)
from app.exceptions import (
    DebtNotFoundError,
    DebtValidationError,
    PaymentValidationError
)

router = APIRouter()

# Debt Endpoints
@router.post("/", response_model=DebtResponse, status_code=status.HTTP_201_CREATED)
async def create_debt(
    debt: DebtCreate,
    user_id: int = Depends(get_current_user_id),
    service: DebtService = Depends(get_debt_service)
):
    """Create a new debt"""
    try:
        return await service.create_debt(debt, user_id)
    except DebtValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[DebtResponse])
def get_debts(
    skip: int = Query(0, ge=0, description="Number of debts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of debts to return"),
    active_only: bool = Query(False, description="Show only active debts"),
    paid_off_only: bool = Query(False, description="Show only paid off debts"),
    user_id: int = Depends(get_current_user_id),
    service: DebtService = Depends(get_debt_service)
):
    """Get all debts for the user"""
    return service.get_debts(user_id, skip, limit, active_only, paid_off_only)

@router.get("/{debt_id}", response_model=DebtResponse)
def get_debt(
    debt_id: int,
    user_id: int = Depends(get_current_user_id),
    service: DebtService = Depends(get_debt_service)
):
    """Get a specific debt"""
    try:
        return service.get_debt(debt_id, user_id)
    except DebtNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/{debt_id}", response_model=DebtResponse)
async def update_debt(
    debt_id: int,
    debt_update: DebtUpdate,
    user_id: int = Depends(get_current_user_id),
    service: DebtService = Depends(get_debt_service)
):
    """Update a debt"""
    try:
        return await service.update_debt(debt_id, debt_update, user_id)
    except DebtNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DebtValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{debt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_debt(
    debt_id: int,
    user_id: int = Depends(get_current_user_id),
    service: DebtService = Depends(get_debt_service)
):
    """Delete a debt"""
    try:
        service.delete_debt(debt_id, user_id)
    except DebtNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DebtValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Payment Endpoints
@router.post("/{debt_id}/payments/", response_model=DebtPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    debt_id: int,
    payment: DebtPaymentCreate,
    user_id: int = Depends(get_current_user_id),
    service: DebtService = Depends(get_debt_service)
):
    """Create a debt payment"""
    try:
        return await service.create_payment(debt_id, payment, user_id)
    except DebtNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PaymentValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{debt_id}/payments/", response_model=List[DebtPaymentResponse])
def get_payments(
    debt_id: int,
    skip: int = Query(0, ge=0, description="Number of payments to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of payments to return"),
    user_id: int = Depends(get_current_user_id),
    service: DebtService = Depends(get_debt_service)
):
    """Get all payments for a debt"""
    try:
        # Verify debt exists and belongs to user
        service.get_debt(debt_id, user_id)
        return service.get_payments(debt_id, user_id, skip, limit)
    except DebtNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# Summary Endpoints
@router.get("/summary/", response_model=DebtSummary)
def get_debt_summary(
    user_id: int = Depends(get_current_user_id),
    service: DebtService = Depends(get_debt_service)
):
    """Get debt summary statistics"""
    return service.get_debt_summary(user_id)