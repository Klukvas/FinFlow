from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func, desc
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from app.models.debt import Debt, DebtPayment
from app.schemas.debt import (
    DebtCreate, DebtUpdate, DebtResponse, DebtSummary,
    DebtPaymentCreate, DebtPaymentResponse
)
from app.services.contact import ContactService
from app.exceptions import (
    DebtNotFoundError,
    DebtValidationError,
    ContactNotFoundError,
    PaymentValidationError,
    ExternalServiceError
)
from app.utils.logger import get_logger, log_operation
from app.config import settings

logger = get_logger(__name__)

class DebtService:
    """Service for managing debts and debt payments"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)
        self.contact_service = ContactService(db)

    # Debt Management
    async def create_debt(self, debt: DebtCreate, user_id: int) -> DebtResponse:
        """Create a new debt"""
        try:
            # Validate contact if provided
            if debt.contact_id:
                self.contact_service.get_contact(debt.contact_id, user_id)  # This will raise if not found
            
            # TODO: Validate category with category service
            # await self._validate_category(debt.category_id, user_id)
            
            db_debt = Debt(
                user_id=user_id,
                name=debt.name,
                description=debt.description,
                debt_type=debt.debt_type.value,
                contact_id=debt.contact_id,
                category_id=debt.category_id,
                initial_amount=debt.initial_amount,
                current_balance=debt.initial_amount,  # Start with initial amount
                interest_rate=debt.interest_rate,
                minimum_payment=debt.minimum_payment,
                start_date=debt.start_date,
                due_date=debt.due_date
            )
            
            self.db.add(db_debt)
            self.db.commit()
            self.db.refresh(db_debt)
            
            # Load contact if available
            if db_debt.contact_id:
                self.db.refresh(db_debt)
            
            log_operation(self.logger, "Debt created", user_id, db_debt.id, f"Name: {debt.name}, Amount: {debt.initial_amount}")
            return DebtResponse.model_validate(db_debt)
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error creating debt: {e}")
            raise DebtValidationError("Failed to create debt")

    def get_debts(self, user_id: int, skip: int = 0, limit: int = 100, 
                  active_only: bool = False, paid_off_only: bool = False) -> List[DebtResponse]:
        """Get all debts for a user"""
        query = self.db.query(Debt).options(joinedload(Debt.contact)).filter(
            Debt.user_id == user_id
        )
        
        if active_only:
            query = query.filter(Debt.is_active == True)
        elif paid_off_only:
            query = query.filter(Debt.is_paid_off == True)
        
        debts = query.offset(skip).limit(limit).all()
        
        return [DebtResponse.model_validate(debt) for debt in debts]

    def get_debt(self, debt_id: int, user_id: int) -> DebtResponse:
        """Get a specific debt"""
        from app.models.debt import Contact
        debt = self.db.query(Debt).options(joinedload(Debt.contact)).filter(
            and_(Debt.id == debt_id, Debt.user_id == user_id)
        ).first()
        
        if not debt:
            raise DebtNotFoundError(debt_id)
        
        return DebtResponse.model_validate(debt)

    async def update_debt(self, debt_id: int, debt_update: DebtUpdate, user_id: int) -> DebtResponse:
        """Update a debt"""
        debt = self.db.query(Debt).filter(
            and_(Debt.id == debt_id, Debt.user_id == user_id)
        ).first()
        
        if not debt:
            raise DebtNotFoundError(debt_id)
        
        try:
            update_data = debt_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field == "debt_type" and value:
                    setattr(debt, field, value.value)
                else:
                    setattr(debt, field, value)
            
            # Check if debt is paid off
            if debt.current_balance <= 0:
                debt.is_paid_off = True
                debt.is_active = False
            
            self.db.commit()
            self.db.refresh(debt)
            
            # Load contact if available
            if debt.contact_id:
                from app.models.debt import Contact
                self.db.refresh(debt)
            
            log_operation(self.logger, "Debt updated", user_id, debt.id, f"Fields: {list(update_data.keys())}")
            return DebtResponse.model_validate(debt)
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error updating debt: {e}")
            raise DebtValidationError("Failed to update debt")

    def delete_debt(self, debt_id: int, user_id: int) -> bool:
        """Delete a debt"""
        debt = self.db.query(Debt).filter(
            and_(Debt.id == debt_id, Debt.user_id == user_id)
        ).first()
        
        if not debt:
            raise DebtNotFoundError(debt_id)
        
        try:
            # Delete associated payments first
            self.db.query(DebtPayment).filter(DebtPayment.debt_id == debt_id).delete()
            
            self.db.delete(debt)
            self.db.commit()
            
            log_operation(self.logger, "Debt deleted", user_id, debt_id, f"Name: {debt.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error deleting debt: {e}")
            raise DebtValidationError("Failed to delete debt")

    # Payment Management
    async def create_payment(self, debt_id: int, payment: DebtPaymentCreate, user_id: int) -> DebtPaymentResponse:
        """Create a debt payment"""
        debt = self.db.query(Debt).filter(
            and_(Debt.id == debt_id, Debt.user_id == user_id)
        ).first()
        
        if not debt:
            raise DebtNotFoundError(debt_id)
        
        try:
            db_payment = DebtPayment(
                debt_id=debt_id,
                user_id=user_id,
                amount=payment.amount,
                principal_amount=payment.principal_amount,
                interest_amount=payment.interest_amount,
                payment_date=payment.payment_date,
                description=payment.description,
                payment_method=payment.payment_method.value if payment.payment_method else None
            )
            
            self.db.add(db_payment)
            
            # Update debt balance
            principal_amount = payment.principal_amount or payment.amount
            debt.current_balance = max(0, debt.current_balance - principal_amount)
            debt.last_payment_date = payment.payment_date
            
            # Check if debt is paid off
            if debt.current_balance <= 0:
                debt.is_paid_off = True
                debt.is_active = False
            
            self.db.commit()
            self.db.refresh(db_payment)
            
            log_operation(self.logger, "Payment created", user_id, db_payment.id, f"Amount: {payment.amount}, Debt: {debt.name}")
            return DebtPaymentResponse.model_validate(db_payment)
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error creating payment: {e}")
            raise PaymentValidationError("Failed to create payment")

    def get_payments(self, debt_id: int, user_id: int, skip: int = 0, limit: int = 100) -> List[DebtPaymentResponse]:
        """Get all payments for a debt"""
        payments = self.db.query(DebtPayment).filter(
            and_(DebtPayment.debt_id == debt_id, DebtPayment.user_id == user_id)
        ).order_by(desc(DebtPayment.payment_date)).offset(skip).limit(limit).all()
        
        return [DebtPaymentResponse.model_validate(payment) for payment in payments]

    # Summary and Statistics
    def get_debt_summary(self, user_id: int) -> DebtSummary:
        """Get debt summary statistics"""
        active_debts = self.db.query(Debt).filter(
            and_(Debt.user_id == user_id, Debt.is_active == True)
        ).all()
        
        paid_off_debts = self.db.query(Debt).filter(
            and_(Debt.user_id == user_id, Debt.is_paid_off == True)
        ).count()
        
        total_debt = sum(debt.current_balance for debt in active_debts)
        
        # Calculate total payments
        total_payments = self.db.query(func.sum(DebtPayment.amount)).filter(
            DebtPayment.user_id == user_id
        ).scalar() or 0
        
        # Calculate average interest rate
        interest_rates = [debt.interest_rate for debt in active_debts if debt.interest_rate is not None]
        avg_interest_rate = sum(interest_rates) / len(interest_rates) if interest_rates else None
        
        return DebtSummary(
            total_debt=total_debt,
            total_payments=total_payments,
            active_debts=len(active_debts),
            paid_off_debts=paid_off_debts,
            average_interest_rate=avg_interest_rate
        )

