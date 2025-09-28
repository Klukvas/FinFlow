from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.clients.category_service_client import CategoryServiceClient
from app.exceptions import (
    ExpenseNotFoundError,
    ExpenseValidationError,
    ExpenseAmountError,
    ExpenseDateError,
    ExpenseDescriptionError,
    ExternalServiceError
)
from app.utils.logger import get_logger, log_operation, log_security_event
from app.config import settings

class ExpenseService:
    def __init__(self, db: Session, category_client: CategoryServiceClient):
        self.db = db
        self.category_client = category_client
        self.logger = get_logger(__name__)

    def _validate_expense_ownership(self, expense_id: int, user_id: int) -> Expense:
        """Validate that expense exists and belongs to user"""
        expense = self.db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == user_id
        ).first()
        if not expense:
            raise ExpenseNotFoundError(expense_id)
        return expense

    def _validate_amount(self, amount: Decimal) -> Decimal:
        """Validate and normalize amount"""
        if amount <= 0:
            raise ExpenseValidationError("Amount must be greater than 0")
        
        if amount > settings.MAX_AMOUNT:
            raise ExpenseAmountError(amount, settings.MAX_AMOUNT)
        
        # Round to 2 decimal places
        return Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _validate_description(self, description: Optional[str]) -> Optional[str]:
        """Validate description length"""
        if description is not None:
            description = description.strip()
            if len(description) > settings.MAX_DESCRIPTION_LENGTH:
                raise ExpenseDescriptionError(len(description), settings.MAX_DESCRIPTION_LENGTH)
            if not description:
                return None
        return description

    def _validate_date(self, expense_date: Optional[date]) -> date:
        """Validate and normalize date"""
        if expense_date is None:
            return date.today()
        
        # Check if date is not in the future
        if expense_date > date.today():
            raise ExpenseValidationError("Expense date cannot be in the future")
        
        # Check if date is not too far in the past (e.g., more than 10 years)
        min_date = date.today().replace(year=date.today().year - 10)
        if expense_date < min_date:
            raise ExpenseValidationError("Expense date cannot be more than 10 years in the past")
        
        return expense_date

    def _validate_category(self, category_id: int, user_id: int) -> dict:
        """Validate category exists and belongs to user"""
        try:
            return self.category_client.validate_category(category_id, user_id)
        except Exception as e:
            self.logger.error(f"Category validation failed: {e}")
            raise

    def create(self, data: ExpenseCreate, user_id: int) -> Expense:
        """Create a new expense with proper validation and transaction management"""
        try:
            # Validate amount
            validated_amount = self._validate_amount(data.amount)
            
            # Validate description
            validated_description = self._validate_description(data.description)
            
            # Validate date
            validated_date = self._validate_date(data.date)
            
            # Validate category
            self._validate_category(data.category_id, user_id)
            
            expense = Expense(
                amount=validated_amount,
                description=validated_description,
                category_id=data.category_id,
                date=validated_date,
                user_id=user_id
            )

            try:
                with self.db.begin():
                    self.db.add(expense)
                log_operation(self.logger, "Expense created", user_id, expense.id, f"Amount: {validated_amount}, Category: {data.category_id}, Date: {validated_date}")
                self.db.refresh(expense)
                return expense
            except Exception as e:
                self.db.rollback()
                raise ExpenseValidationError("Failed to create expense")
            
            
        except (ExpenseValidationError, ExpenseAmountError, ExpenseDateError, 
                ExpenseDescriptionError, ExternalServiceError):
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Database integrity error during expense creation: {e}")
            raise ExpenseValidationError("Database constraint violation")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error during expense creation: {e}")
            raise ExpenseValidationError("Failed to create expense")

    def get_all(self, user_id: int) -> List[Expense]:
        """Get all expenses for the user"""
        try:
            return self.db.query(Expense).filter(Expense.user_id == user_id).order_by(Expense.date.desc()).all()
        except Exception as e:
            self.logger.error(f"Error retrieving expenses: {e}")
            raise ExpenseValidationError("Failed to retrieve expenses")

    def get(self, expense_id: int, user_id: int) -> Expense:
        """Get a specific expense by ID"""
        return self._validate_expense_ownership(expense_id, user_id)

    def update(self, expense_id: int, data: ExpenseUpdate, user_id: int) -> Expense:
        """Update an existing expense with proper validation and transaction management"""
        try:
            expense = self._validate_expense_ownership(expense_id, user_id)
            
            # Track changes for logging
            changes = []
            
            # Validate and update amount if provided
            if data.amount is not None:
                old_amount = expense.amount
                expense.amount = self._validate_amount(data.amount)
                changes.append(f"Amount: {old_amount} -> {expense.amount}")
            
            # Validate and update description if provided
            if data.description is not None:
                old_description = expense.description
                expense.description = self._validate_description(data.description)
                changes.append(f"Description: '{old_description}' -> '{expense.description}'")
            
            # Validate and update date if provided
            if data.date is not None:
                old_date = expense.date
                expense.date = self._validate_date(data.date)
                changes.append(f"Date: {old_date} -> {expense.date}")
            
            # Validate and update category if provided
            if data.category_id is not None:
                old_category = expense.category_id
                self._validate_category(data.category_id, user_id)
                expense.category_id = data.category_id
                changes.append(f"Category: {old_category} -> {data.category_id}")
            
            self.db.commit()
            self.db.refresh(expense)
            
            log_operation(
                self.logger,
                "Expense updated",
                user_id,
                expense_id,
                f"Changes: {', '.join(changes) if changes else 'No changes'}"
            )
            
            return expense
            
        except (ExpenseNotFoundError, ExpenseValidationError, ExpenseAmountError, 
                ExpenseDateError, ExpenseDescriptionError, ExternalServiceError):
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Database integrity error during expense update: {e}")
            raise ExpenseValidationError("Database constraint violation")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error during expense update: {e}")
            raise ExpenseValidationError("Failed to update expense")

    def delete(self, expense_id: int, user_id: int) -> dict:
        """Delete an expense with proper validation and transaction management"""
        try:
            expense = self._validate_expense_ownership(expense_id, user_id)
            
            amount = expense.amount
            category_id = expense.category_id
            expense_date = expense.date
            
            self.db.delete(expense)
            self.db.commit()
            
            log_operation(
                self.logger,
                "Expense deleted",
                user_id,
                expense_id,
                f"Amount: {amount}, Category: {category_id}, Date: {expense_date}"
            )
            
            return {"detail": "Expense deleted successfully"}
            
        except (ExpenseNotFoundError, ExpenseValidationError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error during expense deletion: {e}")
            raise ExpenseValidationError("Failed to delete expense")

    def get_by_category(self, category_id: int, user_id: int) -> List[Expense]:
        """Get all expenses for a specific category"""
        try:
            # First validate the category belongs to the user
            self._validate_category(category_id, user_id)
            
            return self.db.query(Expense).filter(
                Expense.user_id == user_id,
                Expense.category_id == category_id
            ).order_by(Expense.date.desc()).all()
        except Exception as e:
            self.logger.error(f"Error retrieving expenses by category: {e}")
            raise ExpenseValidationError("Failed to retrieve expenses by category")

    def get_by_date_range(self, start_date: date, end_date: date, user_id: int) -> List[Expense]:
        """Get expenses within a date range"""
        try:
            if start_date > end_date:
                raise ExpenseValidationError("Start date cannot be after end date")
            
            return self.db.query(Expense).filter(
                Expense.user_id == user_id,
                Expense.date >= start_date,
                Expense.date <= end_date
            ).order_by(Expense.date.desc()).all()
        except Exception as e:
            self.logger.error(f"Error retrieving expenses by date range: {e}")
            raise ExpenseValidationError("Failed to retrieve expenses by date range")