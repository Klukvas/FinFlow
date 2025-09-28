from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.executor import PaymentExecutor
from app.services.scheduler_service import SchedulerService
from app.services.scheduler_service import scheduler_service
from app.clients.expense_client import ExpenseServiceClient
from app.clients.income_client import IncomeServiceClient
from app.clients.category_client import CategoryServiceClient
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
scheduler = SchedulerService()


@router.post("/execute-recurring-payments")
async def execute_recurring_payments(
    execution_date: Optional[date] = Query(None, description="Дата выполнения (по умолчанию сегодня)"),
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Execute all recurring payments on the specified date (for cron job)"""
    try:
        executed_count = await executor.execute_pending_payments(db, execution_date)
        
        logger.info(f"Executed {executed_count} recurring payments for date {execution_date or date.today()}")
        return {
            "message": f"Successfully executed {executed_count} recurring payments",
            "executed_count": executed_count,
            "execution_date": execution_date or date.today()
        }
    except Exception as e:
        logger.error(f"Failed to execute recurring payments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute recurring payments: {str(e)}")


@router.get("/pending-payments")
async def get_pending_payments(
    execution_date: Optional[date] = Query(None, description="Дата выполнения (по умолчанию сегодня)"),
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Get list of payments that should be executed on the specified date"""
    payments = scheduler.get_payments_to_execute_today(db, execution_date)
    
    return {
        "payments": [payment.to_dict() for payment in payments],
        "count": len(payments),
        "execution_date": execution_date or date.today()
    }


@router.post("/retry-failed-payment/{schedule_id}")
async def retry_failed_payment(
    schedule_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_internal_token)
):
    """Retry failed payment"""
    try:
        success = await executor.retry_failed_payment(db, schedule_id)
        
        if success:
            logger.info(f"Successfully retried failed payment {schedule_id}")
            return {"message": "Payment retry successful"}
        else:
            raise HTTPException(status_code=404, detail="Failed payment not found or cannot be retried")
            
    except Exception as e:
        logger.error(f"Failed to retry payment {schedule_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retry payment: {str(e)}")


@router.get("/scheduler/status")
async def get_scheduler_status(
    _: None = Depends(verify_internal_token)
):
    """Get status of the built-in scheduler"""
    try:
        status = scheduler_service.get_scheduler_status()
        return {
            "status": "success",
            "scheduler": status
        }
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")


@router.post("/scheduler/execute-now")
async def execute_payments_now(
    _: None = Depends(verify_internal_token)
):
    """Execute payments now"""
    try:
        scheduler_service.execute_now()
        return {
            "message": "Manual execution triggered",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Failed to trigger manual execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger manual execution: {str(e)}")


@router.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "service": "recurring-payments",
        "version": "1.0.0"
    }
