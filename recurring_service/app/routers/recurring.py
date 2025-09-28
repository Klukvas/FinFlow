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
from app.dependencies import get_current_user_id

logger = get_logger(__name__)

router = APIRouter(prefix="/recurring-payments", tags=["recurring-payments"])


@router.post("/", response_model=RecurringPaymentResponse)
async def create_recurring_payment(
    payment_data: RecurringPaymentCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create a new recurring payment"""
    try:
        return await recurring_payment_service.create_recurring_payment(payment_data, user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create recurring payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create recurring payment")


@router.get("/", response_model=RecurringPaymentListResponse)
async def get_recurring_payments(
    user_id: int = Depends(get_current_user_id),
    status: Optional[str] = Query(None, description="Filter by status"),
    payment_type: Optional[str] = Query(None, description="Фильтр по типу платежа"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(50, ge=1, le=100, description="Размер страницы"),
    db: Session = Depends(get_db)
):
    """Get list of recurring payments for the user"""
    return recurring_payment_service.get_recurring_payments(
        user_id, db, status, payment_type, page, size
    )


@router.get("/{payment_id}", response_model=RecurringPaymentResponse)
async def get_recurring_payment(
    payment_id: UUID,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get recurring payment by ID"""
    try:
        return recurring_payment_service.get_recurring_payment(payment_id, user_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{payment_id}", response_model=RecurringPaymentResponse)
async def update_recurring_payment(
    payment_id: UUID,
    payment_data: RecurringPaymentUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update recurring payment"""
    try:
        return await recurring_payment_service.update_recurring_payment(
            payment_id, payment_data, user_id, db
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update recurring payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update recurring payment")


@router.delete("/{payment_id}")
async def delete_recurring_payment(
    payment_id: UUID,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Delete recurring payment"""
    try:
        recurring_payment_service.delete_recurring_payment(payment_id, user_id, db)
        return {"message": "Recurring payment deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete recurring payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete recurring payment")


@router.post("/{payment_id}/pause")
async def pause_recurring_payment(
    payment_id: UUID,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Pause recurring payment"""
    try:
        recurring_payment_service.pause_recurring_payment(payment_id, user_id, db)
        return {"message": "Recurring payment paused successfully"}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to pause recurring payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to pause recurring payment")


@router.post("/{payment_id}/resume")
async def resume_recurring_payment(
    payment_id: UUID,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Resume recurring payment"""
    try:
        recurring_payment_service.resume_recurring_payment(payment_id, user_id, db)
        return {"message": "Recurring payment resumed successfully"}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to resume recurring payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resume recurring payment")


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
    try:
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
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get payment schedules: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get payment schedules")


@router.get("/statistics/summary")
async def get_payment_statistics(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get statistics of recurring payments"""
    try:
        return recurring_payment_service.get_payment_statistics(user_id, db)
    except Exception as e:
        logger.error(f"Failed to get payment statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get payment statistics")
