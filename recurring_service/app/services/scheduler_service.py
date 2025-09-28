import asyncio
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.executor import PaymentExecutor
from app.clients.expense_client import ExpenseServiceClient
from app.clients.income_client import IncomeServiceClient
from app.clients.category_client import CategoryServiceClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SchedulerService:
    """Сервис для управления встроенным шедулером"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.executor = None
        self._setup_executor()
    
    def _setup_executor(self):
        """Инициализация executor с клиентами"""
        expense_client = ExpenseServiceClient()
        income_client = IncomeServiceClient()
        category_client = CategoryServiceClient()
        self.executor = PaymentExecutor(expense_client, income_client, category_client)
    
    def start(self):
        """Запустить шедулер"""
        if not self.scheduler.running:
            # Добавить задачу на выполнение каждый день в 00:01
            self.scheduler.add_job(
                self._execute_recurring_payments,
                trigger=CronTrigger(hour=0, minute=1),
                id='execute_recurring_payments',
                name='Execute Recurring Payments',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("Scheduler started - recurring payments will be executed daily at 00:01")
        else:
            logger.warning("Scheduler is already running")
    
    def stop(self):
        """Остановить шедулер"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
        else:
            logger.warning("Scheduler is not running")
    
    async def _execute_recurring_payments(self):
        """Выполнить повторяющиеся платежи (вызывается шедулером)"""
        logger.info("Starting scheduled execution of recurring payments")
        
        db = SessionLocal()
        try:
            executed_count = await self.executor.execute_pending_payments(db)
            logger.info(f"Scheduled execution completed: {executed_count} payments executed")
        except Exception as e:
            logger.error(f"Error during scheduled execution: {str(e)}")
        finally:
            db.close()
    
    def get_scheduler_status(self):
        """Получить статус шедулера"""
        return {
            "running": self.scheduler.running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                }
                for job in self.scheduler.get_jobs()
            ]
        }
    
    def execute_now(self):
        """Выполнить платежи прямо сейчас (для тестирования)"""
        logger.info("Manual execution of recurring payments triggered")
        asyncio.create_task(self._execute_recurring_payments())


# Глобальный экземпляр шедулера
scheduler_service = SchedulerService()
