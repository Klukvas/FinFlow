from datetime import date, datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.recurring_payment import RecurringPayment
from app.models.payment_schedule import PaymentSchedule
from app.schemas.recurring_payment import (
    RecurringPaymentCreate,
    RecurringPaymentUpdate,
    RecurringPaymentResponse,
    RecurringPaymentListResponse,
    RecurringPaymentStatusUpdate
)
from app.schemas.payment_schedule import (
    PaymentScheduleResponse,
    PaymentScheduleListResponse
)
from app.services.payment_calculator import PaymentCalculator
from app.clients.expense_client import ExpenseServiceClient
from app.clients.income_client import IncomeServiceClient
from app.clients.category_client import CategoryServiceClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RecurringPaymentService:
    """Сервис для управления повторяющимися платежами"""
    
    def __init__(self):
        self.expense_client = ExpenseServiceClient()
        self.income_client = IncomeServiceClient()
        self.category_client = CategoryServiceClient()
    
    async def create_recurring_payment(
        self, 
        payment_data: RecurringPaymentCreate, 
        user_id: int, 
        db: Session
    ) -> RecurringPayment:
        """Создать новый повторяющийся платеж"""
        # Валидировать существование категории
        if not await self.category_client.validate_category_exists(payment_data.category_id, user_id):
            raise ValueError("Category not found")

        # Создать модель
        recurring_payment = RecurringPayment(
            user_id=user_id,
            name=payment_data.name,
            description=payment_data.description,
            amount=payment_data.amount,
            currency=payment_data.currency,
            category_id=payment_data.category_id,
            payment_type=payment_data.payment_type,
            schedule_type=payment_data.schedule_type,
            schedule_config=payment_data.schedule_config,
            start_date=payment_data.start_date,
            end_date=payment_data.end_date,
            next_execution=PaymentCalculator.calculate_initial_next_execution(
                payment_data.schedule_type,
                payment_data.schedule_config,
                payment_data.start_date
            )
        )

        db.add(recurring_payment)
        db.commit()
        db.refresh(recurring_payment)

        logger.info(f"Created recurring payment {recurring_payment.id} for user {user_id}")
        return recurring_payment
    
    def get_recurring_payments(
        self,
        user_id: int,
        db: Session,
        status: Optional[str] = None,
        payment_type: Optional[str] = None,
        page: int = 1,
        size: int = 50
    ) -> RecurringPaymentListResponse:
        """Получить список повторяющихся платежей пользователя"""
        query = db.query(RecurringPayment).filter(RecurringPayment.user_id == user_id)

        if status:
            query = query.filter(RecurringPayment.status == status)
        if payment_type:
            query = query.filter(RecurringPayment.payment_type == payment_type)

        total = query.count()
        payments = query.offset((page - 1) * size).limit(size).all()

        return RecurringPaymentListResponse(
            items=payments,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    
    def get_recurring_payment(
        self, 
        payment_id: UUID, 
        user_id: int, 
        db: Session
    ) -> RecurringPayment:
        """Получить повторяющийся платеж по ID"""
        payment = db.query(RecurringPayment).filter(
            RecurringPayment.id == payment_id,
            RecurringPayment.user_id == user_id
        ).first()

        if not payment:
            raise ValueError("Recurring payment not found")

        return payment
    
    async def update_recurring_payment(
        self,
        payment_id: UUID,
        payment_data: RecurringPaymentUpdate,
        user_id: int,
        db: Session
    ) -> RecurringPayment:
        """Обновить повторяющийся платеж"""
        payment = db.query(RecurringPayment).filter(
            RecurringPayment.id == payment_id,
            RecurringPayment.user_id == user_id
        ).first()

        if not payment:
            raise ValueError("Recurring payment not found")

        # Валидировать категорию если она изменилась
        if payment_data.category_id and payment_data.category_id != payment.category_id:
            if not await self.category_client.validate_category_exists(payment_data.category_id, user_id):
                raise ValueError("Category not found")

        # Обновить поля
        update_data = payment_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payment, field, value)

        # Пересчитать дату следующего выполнения если изменились параметры расписания
        if any(field in update_data for field in ['schedule_type', 'schedule_config', 'start_date']):
            payment.next_execution = PaymentCalculator.calculate_initial_next_execution(
                payment.schedule_type,
                payment.schedule_config,
                payment.start_date
            )

        db.commit()
        db.refresh(payment)

        logger.info(f"Updated recurring payment {payment_id} for user {user_id}")
        return payment
    
    def delete_recurring_payment(
        self, 
        payment_id: UUID, 
        user_id: int, 
        db: Session
    ) -> None:
        """Удалить повторяющийся платеж"""
        payment = db.query(RecurringPayment).filter(
            RecurringPayment.id == payment_id,
            RecurringPayment.user_id == user_id
        ).first()

        if not payment:
            raise ValueError("Recurring payment not found")

        db.delete(payment)
        db.commit()

        logger.info(f"Deleted recurring payment {payment_id} for user {user_id}")
    
    def pause_recurring_payment(
        self, 
        payment_id: UUID, 
        user_id: int, 
        db: Session
    ) -> None:
        """Приостановить повторяющийся платеж"""
        payment = db.query(RecurringPayment).filter(
            RecurringPayment.id == payment_id,
            RecurringPayment.user_id == user_id
        ).first()
        
        if not payment:
            raise ValueError("Recurring payment not found")
        
        if payment.status != 'active':
            raise ValueError("Only active payments can be paused")
        
        payment.status = 'paused'
        db.commit()
        db.refresh(payment)

        logger.info(f"Paused recurring payment {payment_id} for user {user_id}")
    
    def resume_recurring_payment(
        self, 
        payment_id: UUID, 
        user_id: int, 
        db: Session
    ) -> None:
        """Возобновить повторяющийся платеж"""
        payment = db.query(RecurringPayment).filter(
            RecurringPayment.id == payment_id,
            RecurringPayment.user_id == user_id
        ).first()
        
        if not payment:
            raise ValueError("Recurring payment not found")
        
        if payment.status != 'paused':
            raise ValueError("Only paused payments can be resumed")
        
        payment.status = 'active'
        db.commit()
        db.refresh(payment)

        logger.info(f"Resumed recurring payment {payment_id} for user {user_id}")
    
    def get_payment_schedules(
        self,
        payment_id: UUID,
        user_id: int,
        db: Session,
        status: Optional[str] = None,
        execution_date_from: Optional[date] = None,
        execution_date_to: Optional[date] = None,
        page: int = 1,
        size: int = 50
    ) -> PaymentScheduleListResponse:
        """Получить расписание выполнения для повторяющегося платежа"""
        # Проверить что платеж принадлежит пользователю
        payment = db.query(RecurringPayment).filter(
            RecurringPayment.id == payment_id,
            RecurringPayment.user_id == user_id
        ).first()

        if not payment:
            raise ValueError("Recurring payment not found")

        # Построить запрос для получения расписаний
        query = db.query(PaymentSchedule).filter(
            PaymentSchedule.recurring_payment_id == payment_id
        )
        
        # Применить фильтры
        if status:
            query = query.filter(PaymentSchedule.status == status)
        if execution_date_from:
            query = query.filter(PaymentSchedule.execution_date >= execution_date_from)
        if execution_date_to:
            query = query.filter(PaymentSchedule.execution_date <= execution_date_to)
        
        # Получить общее количество
        total = query.count()
        
        # Применить пагинацию
        schedules = query.offset((page - 1) * size).limit(size).all()
        
        # Преобразовать в Response объекты
        schedule_responses = [
            PaymentScheduleResponse(
                id=str(schedule.id),
                recurring_payment_id=str(schedule.recurring_payment_id),
                execution_date=schedule.execution_date.isoformat(),
                status=schedule.status,
                amount=float(schedule.amount),
                currency=schedule.currency,
                created_at=schedule.created_at.isoformat(),
                updated_at=schedule.updated_at.isoformat()
            )
            for schedule in schedules
        ]

        return PaymentScheduleListResponse(
            items=schedule_responses,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    
    def get_payment_statistics(
        self, 
        user_id: int, 
        db: Session
    ) -> dict:
        """Получить статистику по повторяющимся платежам"""
        # Общая статистика
        total_payments = db.query(RecurringPayment).filter(
            RecurringPayment.user_id == user_id
        ).count()

        active_payments = db.query(RecurringPayment).filter(
            RecurringPayment.user_id == user_id,
            RecurringPayment.status == "active"
        ).count()

        paused_payments = db.query(RecurringPayment).filter(
            RecurringPayment.user_id == user_id,
            RecurringPayment.status == "paused"
        ).count()

        # Статистика по выполненным платежам за последний месяц
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        executed_this_month = db.query(PaymentSchedule).join(RecurringPayment).filter(
            RecurringPayment.user_id == user_id,
            PaymentSchedule.status == "executed",
            PaymentSchedule.executed_at >= month_ago
        ).count()

        failed_this_month = db.query(PaymentSchedule).join(RecurringPayment).filter(
            RecurringPayment.user_id == user_id,
            PaymentSchedule.status == "failed",
            PaymentSchedule.executed_at >= month_ago
        ).count()

        return {
            "total_payments": total_payments,
            "active_payments": active_payments,
            "paused_payments": paused_payments,
            "executed_this_month": executed_this_month,
            "failed_this_month": failed_this_month
        }


# Глобальный экземпляр сервиса
recurring_payment_service = RecurringPaymentService()

