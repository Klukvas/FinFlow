from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func, desc
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from app.models.debt import Debt, DebtPayment
from app.schemas.debt import (
    DebtCreate, DebtUpdate, DebtResponse, DebtSummary,
    DebtPaymentCreate, DebtPaymentResponse
)
from app.services.contact import ContactService
from app.services.workspace_authorization import WorkspaceAuthorizationMixin
from app.clients.subscription import SubscriptionClient
from app.clients.user_service_client import UserServiceClient
from app.clients.currency_service_client import CurrencyServiceClient
from app.exceptions import (
    DebtNotFoundError,
    DebtValidationError,
    ContactNotFoundError,
    PaymentValidationError,
    ExternalServiceError,
    DebtCreationFailedError,
    DebtUpdateFailedError,
    DebtDeletionFailedError,
    PaymentCreationFailedError,
    DebtLimitExceededError
)
from app.utils.logger import get_logger, log_operation
from app.config import settings

logger = get_logger(__name__)

class DebtService(WorkspaceAuthorizationMixin):
    """Service for managing debts and debt payments"""
    
    def __init__(self, db: Session):
        super().__init__()  # Initialize WorkspaceAuthorizationMixin
        self.db = db
        self.logger = get_logger(__name__)
        self.contact_service = ContactService(db)
        self.subscription_client = SubscriptionClient()
        self.user_client = UserServiceClient()
        self.currency_client = CurrencyServiceClient()

    # Debt Management
    def create_debt(self, debt: DebtCreate, user_id: int, workspace_id: UUID) -> DebtResponse:
        """Create a new debt"""
        try:
            # 1. Authorize workspace access (member role required)
            self.authorize_workspace_access(workspace_id, user_id, "member", "create_debt")
            # Check subscription limits before creating
            current_count = self.db.query(Debt).filter(
                Debt.user_id == user_id,
                Debt.workspace_id == workspace_id
            ).count()
            if not self.subscription_client.check_debt_limit(user_id, current_count):
                features = self.subscription_client.get_user_features(user_id) or {}
                debt_feature = features.get("debts", {})
                limit = debt_feature.get("limit_value", 0)
                raise DebtLimitExceededError(current_count, limit)
            
            # Validate contact if provided
            if debt.contact_id:
                self.contact_service.get_contact(debt.contact_id, user_id)  # This will raise if not found
            
            # TODO: Validate category with category service
            # await self._validate_category(debt.category_id, user_id)
            
            db_debt = Debt(
                user_id=user_id,
                workspace_id=workspace_id,
                name=debt.name,
                description=debt.description,
                debt_type=debt.debt_type.value,
                contact_id=debt.contact_id,
                category_id=debt.category_id,
                currency=debt.currency,
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
            
            log_operation(self.logger, "Debt created", user_id, f"Debt ID: {db_debt.id}, Name: {debt.name}, Amount: {debt.initial_amount}")
            
            # New debt has 0 payments
            debt_dict = DebtResponse.model_validate(db_debt).model_dump()
            debt_dict['payment_count'] = 0
            return DebtResponse.model_validate(debt_dict)
            
        except (DebtLimitExceededError, DebtNotFoundError, DebtValidationError, ContactNotFoundError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error creating debt: {e}")
            raise DebtCreationFailedError("Failed to create debt")

    def get_debts(self, user_id: int, workspace_id: UUID, skip: int = 0, limit: int = 100,
                  active_only: bool = False, paid_off_only: bool = False) -> List[DebtResponse]:
        """Get all debts in the workspace"""
        # 1. Authorize workspace access (viewer role required)
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "list_debts")

        # Subquery for payment counts to avoid N+1
        payment_count_sq = (
            self.db.query(
                DebtPayment.debt_id,
                func.count(DebtPayment.id).label("payment_count")
            )
            .group_by(DebtPayment.debt_id)
            .subquery()
        )

        query = (
            self.db.query(Debt, payment_count_sq.c.payment_count)
            .outerjoin(payment_count_sq, Debt.id == payment_count_sq.c.debt_id)
            .options(joinedload(Debt.contact))
            .filter(and_(Debt.user_id == user_id, Debt.workspace_id == workspace_id))
        )

        if active_only:
            query = query.filter(Debt.is_active == True)
        elif paid_off_only:
            query = query.filter(Debt.is_paid_off == True)

        rows = query.offset(skip).limit(limit).all()

        result = []
        for debt, payment_count in rows:
            debt_dict = DebtResponse.model_validate(debt).model_dump()
            debt_dict['payment_count'] = payment_count or 0
            result.append(DebtResponse.model_validate(debt_dict))

        return result

    def get_debt(self, debt_id: int, user_id: int, workspace_id: UUID) -> DebtResponse:
        """Get a specific debt"""
        # 1. Authorize workspace access (viewer role required)
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_debt")
        from app.models.debt import Contact
        debt = self.db.query(Debt).options(joinedload(Debt.contact)).filter(
            and_(Debt.id == debt_id, Debt.user_id == user_id, Debt.workspace_id == workspace_id)
        ).first()
        
        if not debt:
            raise DebtNotFoundError(debt_id)
        
        debt_dict = DebtResponse.model_validate(debt).model_dump()
        payment_count = self.db.query(DebtPayment).filter(
            DebtPayment.debt_id == debt_id
        ).count()
        debt_dict['payment_count'] = payment_count
        
        return DebtResponse.model_validate(debt_dict)

    def update_debt(self, debt_id: int, debt_update: DebtUpdate, user_id: int, workspace_id: UUID) -> DebtResponse:
        """Update a debt"""
        # 1. Authorize workspace access (member role required)
        self.authorize_workspace_access(workspace_id, user_id, "member", "update_debt")
        
        # 2. Get debt filtered by workspace
        debt = self.db.query(Debt).filter(
            and_(Debt.id == debt_id, Debt.workspace_id == workspace_id)
        ).first()
        
        if not debt:
            raise DebtNotFoundError(debt_id)
        
        # Check if currency is being changed
        update_data = debt_update.model_dump(exclude_unset=True)
        if "currency" in update_data and update_data["currency"] != debt.currency:
            # Check if there are any payments for this debt
            payment_count = self.db.query(DebtPayment).filter(
                DebtPayment.debt_id == debt_id
            ).count()
            
            if payment_count > 0:
                raise DebtValidationError(
                    f"Cannot change currency. This debt has {payment_count} payment(s) already."
                )
        
        try:
            for field, value in update_data.items():
                if field == "debt_type" and value:
                    setattr(debt, field, value.value)
                elif field == "currency" and value:
                    # Validate currency is a valid 3-letter code
                    if len(value) == 3 and value.isupper():
                        setattr(debt, field, value)
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
            
            log_operation(self.logger, "Debt updated", user_id, f"Debt ID: {debt.id}, Fields: {list(update_data.keys())}")
            
            # Add payment count
            debt_dict = DebtResponse.model_validate(debt).model_dump()
            payment_count = self.db.query(DebtPayment).filter(
                DebtPayment.debt_id == debt_id
            ).count()
            debt_dict['payment_count'] = payment_count
            
            return DebtResponse.model_validate(debt_dict)
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error updating debt: {e}")
            raise DebtUpdateFailedError("Failed to update debt")

    def delete_debt(self, debt_id: int, user_id: int, workspace_id: UUID) -> bool:
        """Delete a debt"""
        # 1. Authorize workspace access (member role required)
        self.authorize_workspace_access(workspace_id, user_id, "member", "delete_debt")
        
        # 2. Get debt filtered by workspace
        debt = self.db.query(Debt).filter(
            and_(Debt.id == debt_id, Debt.workspace_id == workspace_id)
        ).first()
        
        if not debt:
            raise DebtNotFoundError(debt_id)
        
        try:
            # Delete associated payments first
            self.db.query(DebtPayment).filter(DebtPayment.debt_id == debt_id).delete()
            
            self.db.delete(debt)
            self.db.commit()
            
            log_operation(self.logger, "Debt deleted", user_id, f"Debt ID: {debt_id}, Name: {debt.name}")
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error deleting debt: {e}")
            raise DebtDeletionFailedError("Failed to delete debt")

    # Payment Management
    def create_payment(self, debt_id: int, payment: DebtPaymentCreate, user_id: int, workspace_id: UUID) -> DebtPaymentResponse:
        """Create a debt payment"""
        # 1. Authorize workspace access (member role required)
        self.authorize_workspace_access(workspace_id, user_id, "member", "create_payment")
        
        # 2. Get debt filtered by workspace
        debt = self.db.query(Debt).filter(
            and_(Debt.id == debt_id, Debt.workspace_id == workspace_id)
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
            
            log_operation(self.logger, "Payment created", user_id, f"Payment ID: {db_payment.id}, Amount: {payment.amount}, Debt: {debt.name}")
            return DebtPaymentResponse.model_validate(db_payment)
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error creating payment: {e}")
            raise PaymentCreationFailedError("Failed to create payment")

    def get_payments(self, debt_id: int, user_id: int, skip: int = 0, limit: int = 100) -> List[DebtPaymentResponse]:
        """Get all payments for a debt"""
        payments = self.db.query(DebtPayment).filter(
            and_(DebtPayment.debt_id == debt_id, DebtPayment.user_id == user_id)
        ).order_by(desc(DebtPayment.payment_date)).offset(skip).limit(limit).all()
        
        return [DebtPaymentResponse.model_validate(payment) for payment in payments]

    # Summary and Statistics
    def get_debt_summary(self, user_id: int, workspace_id: UUID) -> DebtSummary:
        """Get debt summary statistics with currency conversion"""
        # 1. Authorize workspace access (viewer role required)
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_debt_summary")
        # Get user's base currency
        try:
            user_currency = self.user_client.get_user_base_currency(user_id)
        except Exception as e:
            self.logger.warning(f"Could not fetch user currency for user {user_id}: {str(e)}, defaulting to USD")
            user_currency = settings.DEFAULT_CURRENCY

        active_debts = self.db.query(Debt).filter(
            and_(Debt.workspace_id == workspace_id, Debt.is_active == True)
        ).all()
        
        paid_off_debts = self.db.query(Debt).filter(
            and_(Debt.workspace_id == workspace_id, Debt.is_paid_off == True)
        ).count()
        
        # Convert and sum all debts to user's currency
        total_debt = 0.0
        for debt in active_debts:
            debt_amount = abs(debt.current_balance)  # Use absolute value
            debt_currency = debt.currency or settings.DEFAULT_CURRENCY
            
            if debt_currency != user_currency:
                # Convert to user's currency
                converted_amount = self.currency_client.convert_amount(
                    debt_amount, debt_currency, user_currency
                )
                if converted_amount is not None:
                    debt_amount = converted_amount
            
            total_debt += debt_amount
        
        # Calculate total payments with currency conversion
        # Get all debts (not just active ones) to get payment currencies
        # 2. Get all debts in workspace
        all_debts = self.db.query(Debt).filter(Debt.workspace_id == workspace_id).all()
        debt_currency_map = {debt.id: debt.currency or settings.DEFAULT_CURRENCY for debt in all_debts}
        
        all_payments = self.db.query(DebtPayment).filter(
            DebtPayment.user_id == user_id
        ).all()
        
        total_payments = 0.0
        for payment in all_payments:
            # Get the debt currency from the map
            payment_currency = debt_currency_map.get(payment.debt_id, settings.DEFAULT_CURRENCY)
            payment_amount = payment.amount
            
            if payment_currency != user_currency:
                # Convert to user's currency
                converted_amount = self.currency_client.convert_amount(
                    payment_amount, payment_currency, user_currency
                )
                if converted_amount is not None:
                    payment_amount = converted_amount
            
            total_payments += payment_amount
        
        # Calculate average interest rate
        interest_rates = [debt.interest_rate for debt in active_debts if debt.interest_rate is not None]
        avg_interest_rate = sum(interest_rates) / len(interest_rates) if interest_rates else None
        
        return DebtSummary(
            total_debt=round(total_debt, 2),
            total_payments=round(total_payments, 2),
            active_debts=len(active_debts),
            paid_off_debts=paid_off_debts,
            currency=user_currency,
            average_interest_rate=avg_interest_rate
        )

