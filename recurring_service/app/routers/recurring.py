from datetime import date
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.recurring_payment import (
    RecurringPaymentCreate,
    RecurringPaymentUpdate,
    RecurringPaymentResponse,
    RecurringPaymentListResponse,
)
from app.schemas.payment_schedule import (
    PaymentScheduleListResponse
)
from app.services.recurring_payment_service import recurring_payment_service
from app.utils.logger import get_logger
from app.dependencies import get_current_user_id, get_workspace_id

logger = get_logger(__name__)

router = APIRouter(prefix="/recurring-payments", tags=["recurring-payments"])


@router.post("/", response_model=RecurringPaymentResponse)
async def create_recurring_payment(
    payment_data: RecurringPaymentCreate,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    db: Session = Depends(get_db)
):
    """Create a new recurring payment. Requires 'member' role."""
    return await recurring_payment_service.create_recurring_payment(payment_data, user_id, workspace_id, db)


@router.get("/", response_model=RecurringPaymentListResponse)
async def get_recurring_payments(
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    status: Optional[str] = Query(None, description="Filter by status"),
    payment_type: Optional[str] = Query(None, description="Фильтр по типу платежа"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(50, ge=1, le=100, description="Размер страницы"),
    db: Session = Depends(get_db)
):
    """Get list of recurring payments in workspace. Requires 'viewer' role."""
    return recurring_payment_service.get_recurring_payments(
        user_id, workspace_id, db, status, payment_type, page, size
    )


@router.get("/{payment_id}", response_model=RecurringPaymentResponse)
async def get_recurring_payment(
    payment_id: UUID,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    db: Session = Depends(get_db)
):
    """Get recurring payment by ID. Requires 'viewer' role."""
    return recurring_payment_service.get_recurring_payment(payment_id, user_id, workspace_id, db)


@router.put("/{payment_id}", response_model=RecurringPaymentResponse)
async def update_recurring_payment(
    payment_id: UUID,
    payment_data: RecurringPaymentUpdate,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    db: Session = Depends(get_db)
):
    """Update recurring payment. Requires 'member' role."""
    return await recurring_payment_service.update_recurring_payment(
        payment_id, payment_data, user_id, workspace_id,
        payment_id, payment_data, user_id, db
    )


@router.delete("/{payment_id}")
async def delete_recurring_payment(
    payment_id: UUID,
    user_id: int = Depends(get_current_user_id),
    workspace_id: UUID = Depends(get_workspace_id),
    db: Session = Depends(get_db)
):
    """Delete recurring payment. Requires 'member' role."""
    recurring_payment_service.delete_recurring_payment(payment_id, user_id, workspace_id, db)
    return {"message": "Recurring payment deleted successfully"}


@router.post("/{payment_id}/pause")
async def pause_recurring_payment(
    payment_id: UUID,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Pause recurring payment"""
    recurring_payment_service.pause_recurring_payment(payment_id, user_id, db)
    return {"message": "Recurring payment paused successfully"}


@router.post("/{payment_id}/resume")
async def resume_recurring_payment(
    payment_id: UUID,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Resume recurring payment"""
    recurring_payment_service.resume_recurring_payment(payment_id, user_id, db)
    return {"message": "Recurring payment resumed successfully"}


@router.get("/{payment_id}/schedules", response_model=PaymentScheduleListResponse)
async def get_payment_schedules(
    payment_id: UUID,
    user_id: int = Depends(get_current_user_id),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    execution_date_from: Optional[date] = Query(None, description="Дата выполнения от"),
    execution_date_to: Optional[date] = Query(None, description="Дата выполнения до"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(50, ge=1, le=100, description="Размер страницы"),
    db: Session = Depends(get_db)
):
    """Get schedule of execution for recurring payment"""
    return recurring_payment_service.get_payment_schedules(
        payment_id, 
        user_id, 
        db, 
        status, 
        execution_date_from, 
        execution_date_to, 
        page, 
        size
    )


@router.get("/statistics/summary")
async def get_payment_statistics(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get statistics of recurring payments"""
    return recurring_payment_service.get_payment_statistics(user_id, db)
