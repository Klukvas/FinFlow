from datetime import date
from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.recurring_payment import RecurringPayment
from app.services.executor import PaymentExecutor
from app.services.scheduler_service import scheduler_service
from app.clients.expense_client import ExpenseServiceClient
from app.clients.income_client import IncomeServiceClient
from app.clients.category_client import CategoryServiceClient
from app.exceptions import (
    PaymentExecutionError,
    ScheduleNotFoundError,
    InternalServerError
)
from app.utils.logger import get_logger
from app.dependencies import verify_internal_token

logger = get_logger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])

# Инициализация клиентов
expense_client = ExpenseServiceClient()
income_client = IncomeServiceClient()
category_client = CategoryServiceClient()

# Инициализация сервисов
executor = PaymentExecutor(expense_client, income_client, category_client)


@router.post("/execute-recurring-payments")
async def execute_recurring_payments(
    execution_date: Optional[date] = Query(None, description="Дата выполнения (по умолчанию сегодня)"),
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Execute all recurring payments on the specified date (for cron job)"""
    result = await executor.execute_pending_payments(db, execution_date)

    logger.info(f"Executed recurring payments for date {execution_date or date.today()}: {result['succeeded']} succeeded, {result['failed']} failed")
    return {
        "message": f"Executed {result['succeeded']} recurring payments ({result['failed']} failed)",
        "succeeded": result["succeeded"],
        "failed": result["failed"],
        "execution_date": execution_date or date.today()
    }


@router.get("/pending-payments")
async def get_pending_payments(
    execution_date: Optional[date] = Query(None, description="Дата выполнения (по умолчанию сегодня)"),
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Get list of payments that should be executed on the specified date"""
    target_date = execution_date or date.today()
    payments = db.query(RecurringPayment).filter(
        RecurringPayment.status == "active",
        RecurringPayment.next_execution <= target_date,
        RecurringPayment.end_date.is_(None) | (RecurringPayment.end_date >= target_date)
    ).all()

    return {
        "payments": [payment.to_dict() for payment in payments],
        "count": len(payments),
        "execution_date": target_date
    }


@router.post("/retry-failed-payment/{schedule_id}")
async def retry_failed_payment(
    schedule_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Retry failed payment"""
    success = await executor.retry_failed_payment(db, schedule_id)
    
    if success:
        logger.info(f"Successfully retried failed payment {schedule_id}")
        return {"message": "Payment retry successful"}
    else:
        raise ScheduleNotFoundError("Failed payment not found or cannot be retried")


@router.get("/scheduler/status")
async def get_scheduler_status(
    _: None = Depends(verify_internal_token)
):
    """Get status of the built-in scheduler"""
    status = scheduler_service.get_scheduler_status()
    return {
        "status": "success",
        "scheduler": status
    }


@router.post("/scheduler/execute-now")
async def execute_payments_now(
    _: None = Depends(verify_internal_token)
):
    """Execute payments now"""
    scheduler_service.execute_now()
    return {
        "message": "Manual execution triggered",
        "status": "success"
    }


@router.get("/recurring/ai-summary")
async def get_recurring_ai_summary(
    user_id: Annotated[int, Query(description="User ID", gt=0)],
    workspace_id: Annotated[UUID, Query(description="Workspace ID")],
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token),
) -> dict:
    """
    Internal endpoint returning all active recurring payments for AI analysis.

    Returns aggregated data without PII for the AI assistant to analyze
    recurring payment patterns and provide financial insights.
    """
    try:
        payments = (
            db.query(RecurringPayment)
            .filter(
                RecurringPayment.user_id == user_id,
                RecurringPayment.workspace_id == workspace_id,
                RecurringPayment.status == "active",
            )
            .limit(500)
            .all()
        )
        return {
            "items": [
                {
                    "name": p.name,
                    "amount": float(p.amount),
                    "currency": p.currency,
                    "category_id": p.category_id,
                    "payment_type": p.payment_type,
                    "schedule_type": p.schedule_type,
                    "next_execution": str(p.next_execution) if p.next_execution else None,
                }
                for p in payments
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching recurring AI summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recurring payments summary",
        )


@router.get("/health")
def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "recurring-payments",
        "version": "1.0.0"
    }
