from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Optional
from datetime import datetime, date
from app.models.income import Income
from app.schemas.income import IncomeCreate, IncomeUpdate, IncomeOut, IncomeSummary, IncomeStats
from app.exceptions import (
    IncomeNotFoundError,
    IncomeValidationError,
    IncomeAmountError,
    IncomeDateError,
    IncomeDescriptionError,
    ExternalServiceError
)
from app.clients.category_service_client import CategoryServiceClient
from app.clients.account_service_client import AccountServiceClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

class IncomeService:
    """Service for managing incomes"""
    
    def __init__(self, db: Session, account_client: AccountServiceClient = None):
        self.db = db
        self.category_client = CategoryServiceClient()
        self.account_client = account_client or AccountServiceClient()
    
    async def _validate_category(self, category_id: int, user_id: int) -> dict:
        """Validate category exists and belongs to user"""
        try:
            return await self.category_client.validate_category(category_id, user_id)
        except Exception as e:
            logger.error(f"Category validation failed: {e}")
            raise

    async def _validate_account(self, account_id: int, user_id: int) -> dict:
        """Validate account exists and belongs to user"""
        try:
            return await self.account_client.validate_account(account_id, user_id)
        except Exception as e:
            logger.error(f"Account validation failed: {e}")
            raise

    async def _handle_balance_updates(self, income: Income, old_amount: float, old_account_id: int, user_id: int) -> None:
        """Handle account balance updates when income amount or account changes"""
        try:
            # If account changed or amount changed, we need to update balances
            if income.account_id != old_account_id or income.amount != old_amount:
                
                # Restore balance to old account if it had one (subtract old amount)
                if old_account_id is not None:
                    await self.account_client.update_account_balance(old_account_id, user_id, -old_amount, income.currency)
                    logger.info(f"Restored {old_amount} {income.currency} from account {old_account_id}")
                
                # Add to new account if it has one (add new amount)
                if income.account_id is not None:
                    await self.account_client.update_account_balance(income.account_id, user_id, income.amount, income.currency)
                    logger.info(f"Added {income.amount} {income.currency} to account {income.account_id}")
                    
        except Exception as e:
            logger.error(f"Failed to handle balance updates: {e}")
            raise IncomeValidationError("Failed to update account balances")
    
    async def create(self, income: IncomeCreate, user_id: int) -> IncomeOut:
        """Create a new income"""
        try:
            # Validate amount
            if income.amount <= 0:
                raise IncomeAmountError("Income amount must be greater than 0")
            
            if income.amount > 999999.99:
                raise IncomeAmountError("Income amount cannot exceed 999,999.99")
            
            # Validate date
            if income.date:
                try:
                    income_date = date.fromisoformat(income.date)
                    if income_date > datetime.now().date():
                        raise IncomeDateError("Income date cannot be in the future")
                except ValueError:
                    raise IncomeDateError("Invalid date format. Use YYYY-MM-DD format")
            
            # Validate description
            if income.description and len(income.description) > 500:
                raise IncomeDescriptionError("Description cannot exceed 500 characters")
            
            # Validate category if provided
            if income.category_id:
                await self._validate_category(income.category_id, user_id)
            
            # Validate account if provided and update balance
            if income.account_id is not None:
                await self._validate_account(income.account_id, user_id)
                # Add amount to account balance with currency conversion
                await self.account_client.update_account_balance(income.account_id, user_id, income.amount, income.currency)
            
            # Create income
            income_date = datetime.now()
            if income.date:
                try:
                    income_date = datetime.fromisoformat(income.date)
                except ValueError:
                    raise IncomeDateError("Invalid date format. Use YYYY-MM-DD format")
            
            db_income = Income(
                user_id=user_id,
                amount=round(income.amount, 2),
                category_id=income.category_id,
                account_id=income.account_id,
                currency=income.currency,
                description=income.description,
                date=income_date
            )
            
            self.db.add(db_income)
            self.db.commit()
            self.db.refresh(db_income)
            
            logger.info(f"Created income {db_income.id} for user {user_id}")
            return IncomeOut.model_validate(db_income)
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (IncomeAmountError, IncomeDateError, IncomeDescriptionError, IncomeValidationError)):
                raise
            logger.error(f"Error creating income: {e}")
            raise IncomeValidationError("Failed to create income")
    
    def get_by_id(self, income_id: int, user_id: int) -> IncomeOut:
        """Get income by ID"""
        income = self.db.query(Income).filter(
            and_(Income.id == income_id, Income.user_id == user_id)
        ).first()
        
        if not income:
            raise IncomeNotFoundError(f"Income {income_id} not found")
        
        return IncomeOut.from_orm(income)
    
    def get_all(self, user_id: int, skip: int = 0, limit: int = 100) -> List[IncomeOut]:
        """Get all incomes for user"""
        incomes = self.db.query(Income).filter(
            Income.user_id == user_id
        ).order_by(desc(Income.date)).offset(skip).limit(limit).all()
        
        return [IncomeOut.from_orm(income) for income in incomes]
    
    async def update(self, income_id: int, income_update: IncomeUpdate, user_id: int) -> IncomeOut:
        """Update income"""
        db_income = self.db.query(Income).filter(
            and_(Income.id == income_id, Income.user_id == user_id)
        ).first()
        
        if not db_income:
            raise IncomeNotFoundError(f"Income {income_id} not found")
        
        try:
            # Store original values for balance calculations
            old_amount = db_income.amount
            old_account_id = db_income.account_id
            
            # Update fields if provided
            if income_update.amount is not None:
                if income_update.amount <= 0:
                    raise IncomeAmountError("Income amount must be greater than 0")
                if income_update.amount > 999999.99:
                    raise IncomeAmountError("Income amount cannot exceed 999,999.99")
                db_income.amount = round(income_update.amount, 2)
            
            if income_update.date is not None:
                if income_update.date > datetime.now():
                    raise IncomeDateError("Income date cannot be in the future")
                db_income.date = income_update.date
            
            if income_update.description is not None:
                if len(income_update.description) > 500:
                    raise IncomeDescriptionError("Description cannot exceed 500 characters")
                db_income.description = income_update.description
            
            if income_update.category_id is not None:
                # Validate category if provided
                if income_update.category_id > 0:
                    try:
                        # Note: This would need to be async in real implementation
                        pass  # await category_client.get(f"/internal/categories/{income_update.category_id}", {"user_id": user_id})
                    except Exception as e:
                        logger.warning(f"Category validation failed: {e}")
                        raise IncomeValidationError("Invalid category ID")
                db_income.category_id = income_update.category_id
            
            if income_update.account_id is not None:
                # Validate account if provided
                if income_update.account_id > 0:
                    await self._validate_account(income_update.account_id, user_id)
                db_income.account_id = income_update.account_id
            
            if income_update.currency is not None:
                db_income.currency = income_update.currency
            
            # Handle account balance updates
            await self._handle_balance_updates(db_income, old_amount, old_account_id, user_id)
            
            db_income.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(db_income)
            
            logger.info(f"Updated income {income_id} for user {user_id}")
            return IncomeOut.from_orm(db_income)
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (IncomeAmountError, IncomeDateError, IncomeDescriptionError, IncomeValidationError)):
                raise
            logger.error(f"Error updating income: {e}")
            raise IncomeValidationError("Failed to update income")
    
    async def delete(self, income_id: int, user_id: int) -> bool:
        """Delete income"""
        db_income = self.db.query(Income).filter(
            and_(Income.id == income_id, Income.user_id == user_id)
        ).first()
        
        if not db_income:
            raise IncomeNotFoundError(f"Income {income_id} not found")
        
        # Restore balance to account if income had one (subtract the amount)
        if db_income.account_id is not None:
            await self.account_client.update_account_balance(db_income.account_id, user_id, -db_income.amount, db_income.currency)
            logger.info(f"Restored {db_income.amount} {db_income.currency} from account {db_income.account_id} after income deletion")
        
        self.db.delete(db_income)
        self.db.commit()
        
        logger.info(f"Deleted income {income_id} for user {user_id}")
        return True
    
    def get_summary(self, user_id: int, start_date: datetime, end_date: datetime) -> IncomeSummary:
        """Get income summary for date range"""
        incomes = self.db.query(Income).filter(
            and_(
                Income.user_id == user_id,
                Income.date >= start_date,
                Income.date <= end_date
            )
        ).all()
        
        total_income = sum(income.amount for income in incomes)
        count = len(incomes)
        average_income = total_income / count if count > 0 else 0
        
        return IncomeSummary(
            total_income=total_income,
            count=count,
            average_income=average_income,
            period_start=start_date,
            period_end=end_date
        )
    
    def get_stats(self, user_id: int) -> IncomeStats:
        """Get income statistics for user"""
        now = datetime.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Total income
        total_income = self.db.query(func.sum(Income.amount)).filter(
            Income.user_id == user_id
        ).scalar() or 0
        
        # Monthly income
        monthly_income = self.db.query(func.sum(Income.amount)).filter(
            and_(
                Income.user_id == user_id,
                Income.date >= current_month_start
            )
        ).scalar() or 0
        
        # Yearly income
        yearly_income = self.db.query(func.sum(Income.amount)).filter(
            and_(
                Income.user_id == user_id,
                Income.date >= current_year_start
            )
        ).scalar() or 0
        
        # Count and average
        income_count = self.db.query(func.count(Income.id)).filter(
            Income.user_id == user_id
        ).scalar() or 0
        
        average_income = total_income / income_count if income_count > 0 else 0
        
        return IncomeStats(
            total_income=total_income,
            monthly_income=monthly_income,
            yearly_income=yearly_income,
            income_count=income_count,
            average_income=average_income
        )
