from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.recurring_payment import RecurringPayment
from app.models.payment_schedule import PaymentSchedule
from app.services.payment_calculator import PaymentCalculator
from app.clients.expense_client import ExpenseServiceClient
from app.clients.income_client import IncomeServiceClient
from app.clients.category_client import CategoryServiceClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PaymentExecutor:
    """Сервис для выполнения повторяющихся платежей"""

    def __init__(
        self,
        expense_client: ExpenseServiceClient,
        income_client: IncomeServiceClient,
        category_client: CategoryServiceClient
    ):
        self.expense_client = expense_client
        self.income_client = income_client
        self.category_client = category_client

    async def execute_pending_payments(self, db: Session, execution_date: Optional[date] = None) -> int:
        """Выполнить все ожидающие платежи на указанную дату"""
        if execution_date is None:
            execution_date = date.today()

        # Найти все активные повторяющиеся платежи, которые должны выполняться сегодня
        recurring_payments = db.query(RecurringPayment).filter(
            RecurringPayment.status == "active",
            RecurringPayment.next_execution <= execution_date,
            RecurringPayment.end_date.is_(None) | (RecurringPayment.end_date >= execution_date)
        ).all()
        logger.info(f"Found {len(recurring_payments)} recurring payments to execute")

        executed_count = 0
        for recurring_payment in recurring_payments:
            try:
                await self._execute_single_payment(db, recurring_payment, execution_date)
                executed_count += 1
                logger.info(f"Successfully executed recurring payment {recurring_payment.id}")
            except Exception as e:
                logger.error(f"Failed to execute recurring payment {recurring_payment.id}: {str(e)}")
                await self._create_failed_schedule(db, recurring_payment, execution_date, str(e))

        return executed_count

    async def _execute_single_payment(
        self, 
        db: Session, 
        recurring_payment: RecurringPayment, 
        execution_date: date
    ) -> None:
        """Выполнить один повторяющийся платеж"""
        # Создать запись в расписании
        schedule = PaymentSchedule(
            recurring_payment_id=recurring_payment.id,
            execution_date=execution_date,
            status="pending"
        )
        db.add(schedule)
        db.flush()

        try:
            # Валидировать категорию
            await self.category_client.get_category(recurring_payment.category_id, recurring_payment.user_id)

            # Создать expense или income
            if recurring_payment.payment_type == "EXPENSE":
                expense_data = {
                    "amount": float(recurring_payment.amount),
                    "category_id": recurring_payment.category_id,
                    "description": f"Автоматический платеж: {recurring_payment.name}",
                    "date": execution_date.isoformat(),
                }
                expense_response = await self.expense_client.create_expense(expense_data, recurring_payment.user_id)
                schedule.created_expense_id = UUID(expense_response["id"])
            else:  # income
                income_data = {
                    "amount": float(recurring_payment.amount),
                    "category_id": recurring_payment.category_id,
                    "description": f"Автоматический доход: {recurring_payment.name}",
                    "date": execution_date.isoformat()
                }
                income_response = await self.income_client.create_income(income_data, recurring_payment.user_id)
                schedule.created_income_id = UUID(income_response["id"])

            # Обновить статус расписания
            schedule.status = "executed"
            schedule.executed_at = datetime.utcnow()

            # Обновить повторяющийся платеж
            recurring_payment.last_executed = datetime.utcnow()
            recurring_payment.next_execution = PaymentCalculator.calculate_next_execution(recurring_payment)

            # Если достигнута дата окончания, завершить платеж
            if recurring_payment.end_date and recurring_payment.next_execution > recurring_payment.end_date:
                recurring_payment.status = "completed"

            db.commit()

        except Exception as e:
            # Обновить статус расписания на failed
            schedule.status = "failed"
            schedule.error_message = str(e)
            db.commit()
            raise

    async def _create_failed_schedule(
        self, 
        db: Session, 
        recurring_payment: RecurringPayment, 
        execution_date: date, 
        error_message: str
    ) -> None:
        """Создать запись о неудачном выполнении платежа"""
        schedule = PaymentSchedule(
            recurring_payment_id=recurring_payment.id,
            execution_date=execution_date,
            status="failed",
            error_message=error_message
        )
        db.add(schedule)
        db.commit()

    async def retry_failed_payment(self, db: Session, schedule_id: UUID) -> bool:
        """Повторить неудачный платеж"""
        schedule = db.query(PaymentSchedule).filter(
            PaymentSchedule.id == schedule_id,
            PaymentSchedule.status == "failed"
        ).first()

        if not schedule:
            return False

        recurring_payment = db.query(RecurringPayment).filter(
            RecurringPayment.id == schedule.recurring_payment_id
        ).first()

        if not recurring_payment or recurring_payment.status != "active":
            return False

        try:
            await self._execute_single_payment(db, recurring_payment, schedule.execution_date)
            return True
        except Exception as e:
            logger.error(f"Retry failed for schedule {schedule_id}: {str(e)}")
            schedule.error_message = f"Retry failed: {str(e)}"
            db.commit()
            return False
