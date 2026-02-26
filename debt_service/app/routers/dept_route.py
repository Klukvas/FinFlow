
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.dependencies import get_debt_service, get_current_user_id, get_workspace_id
from app.services.debt import DebtService
from app.schemas.debt import (
    DebtCreate, DebtUpdate, DebtResponse, DebtSummary,
    DebtPaymentCreate, DebtPaymentResponse
)

router = APIRouter()

# Debt Endpoints
@router.post("/", response_model=DebtResponse, status_code=status.HTTP_201_CREATED)
def create_debt(
    debt: DebtCreate,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: DebtService = Depends(get_debt_service)
):
    """Create a new debt. Requires 'member' role."""
    return service.create_debt(debt, user_id, workspace_id)

@router.get("/", response_model=List[DebtResponse])
def get_debts(
    skip: int = Query(0, ge=0, description="Number of debts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of debts to return"),
    active_only: bool = Query(False, description="Show only active debts"),
    paid_off_only: bool = Query(False, description="Show only paid off debts"),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: DebtService = Depends(get_debt_service)
):
    """Get all debts in the workspace. Requires 'viewer' role."""
    debts = service.get_debts(user_id, workspace_id, skip, limit, active_only, paid_off_only)

    ordered_ids = service._get_ordered_ids(workspace_id)
    read_only_ids = service.subscription_client.get_read_only_ids(user_id, "debts", ordered_ids)
    for debt in debts:
        debt.is_read_only = debt.id in read_only_ids

    return debts

@router.get("/{debt_id}", response_model=DebtResponse)
def get_debt(
    debt_id: int,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: DebtService = Depends(get_debt_service)
):
    """Get a specific debt. Requires 'viewer' role."""
    return service.get_debt(debt_id, user_id, workspace_id)

@router.put("/{debt_id}", response_model=DebtResponse)
def update_debt(
    debt_id: int,
    debt_update: DebtUpdate,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: DebtService = Depends(get_debt_service)
):
    """Update a debt. Requires 'member' role."""
    return service.update_debt(debt_id, debt_update, user_id, workspace_id)

@router.delete("/{debt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_debt(
    debt_id: int,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: DebtService = Depends(get_debt_service)
):
    """Delete a debt. Requires 'member' role."""
    service.delete_debt(debt_id, user_id, workspace_id)

# Payment Endpoints
@router.post("/{debt_id}/payments/", response_model=DebtPaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    debt_id: int,
    payment: DebtPaymentCreate,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: DebtService = Depends(get_debt_service)
):
    """Create a debt payment. Requires 'member' role."""
    return service.create_payment(debt_id, payment, user_id, workspace_id)

@router.get("/{debt_id}/payments/", response_model=List[DebtPaymentResponse])
def get_payments(
    debt_id: int,
    skip: int = Query(0, ge=0, description="Number of payments to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of payments to return"),
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: DebtService = Depends(get_debt_service)
):
    """Get all payments for a debt. Requires 'viewer' role."""
    # Verify debt exists and belongs to workspace
    service.get_debt(debt_id, user_id, workspace_id)
    return service.get_payments(debt_id, user_id, skip, limit)

# Summary Endpoints
@router.get("/summary/", response_model=DebtSummary)
def get_debt_summary(
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    service: DebtService = Depends(get_debt_service)
):
    """Get debt summary statistics. Requires 'viewer' role."""
    return service.get_debt_summary(user_id, workspace_id)