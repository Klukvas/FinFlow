from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from typing import List, Optional
from datetime import datetime, date
from uuid import UUID
from app.models.income import Income
from app.schemas.income import IncomeCreate, IncomeUpdate, IncomeOut, IncomeSummary, IncomeStats, CategoryIncomeStatistics, IncomesByCategoryResponse
from app.exceptions import (
    IncomeNotFoundError,
    IncomeValidationError,
    IncomeAmountError,
    IncomeDateError,
    IncomeDescriptionError,
    ExternalServiceError,
    IncomeLimitExceededError,
    IncomeErrorCodes
)
from app.clients.category_service_client import CategoryServiceClient
from app.clients.account_service_client import AccountServiceClient
from app.clients.currency_service_client import CurrencyServiceClient
from shared.clients import SubscriptionClient
from shared.auth import WorkspaceAuthorizationMixin
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)

class IncomeService(WorkspaceAuthorizationMixin):
    """Service for managing incomes"""
    
    def __init__(self, db: Session, account_client: AccountServiceClient = None):
        super().__init__(
            access_denied_error=IncomeValidationError,
            workspace_mismatch_error=IncomeValidationError,
        )
        self.db = db
        self.category_client = CategoryServiceClient()
        self.account_client = account_client or AccountServiceClient()
        self.currency_client = CurrencyServiceClient()
        self.subscription_client = SubscriptionClient.get_instance()
    
    async def _validate_category(self, category_id: int, user_id: int, workspace_id: UUID) -> dict:
        """Validate category exists and belongs to user in the workspace"""
        try:
            return await self.category_client.validate_category(category_id, user_id, workspace_id)
        except Exception as e:
            logger.error(f"Category validation failed: {e}")
            raise ExternalServiceError(f"Category validation failed: {e}", "category_service", IncomeErrorCodes.CATEGORY_VALIDATION_FAILED)

    async def _validate_account(self, account_id: int, user_id: int, workspace_id: UUID = None) -> dict:
        """Validate account exists and belongs to user"""
        try:
            return await self.account_client.validate_account(account_id, user_id, workspace_id)
        except Exception as e:
            logger.error(f"Account validation failed: {e}")
            raise ExternalServiceError(f"Account validation failed: {e}", "account_service", IncomeErrorCodes.ACCOUNT_VALIDATION_FAILED)

    async def _handle_balance_updates(self, income: Income, old_amount: float, old_account_id: int, user_id: int, workspace_id: UUID = None) -> None:
        """Handle account balance updates when income amount or account changes"""
        try:
            # If account changed or amount changed, we need to update balances
            if income.account_id != old_account_id or income.amount != old_amount:

                # Restore balance to old account if it had one (subtract old amount)
                if old_account_id is not None:
                    await self.account_client.update_account_balance(old_account_id, user_id, -old_amount, income.currency, workspace_id)
                    logger.info(f"Restored {old_amount} {income.currency} from account {old_account_id}")

                # Add to new account if it has one (add new amount)
                if income.account_id is not None:
                    await self.account_client.update_account_balance(income.account_id, user_id, income.amount, income.currency, workspace_id)
                    logger.info(f"Added {income.amount} {income.currency} to account {income.account_id}")
                    
        except Exception as e:
            logger.error(f"Failed to handle balance updates: {e}")
            raise IncomeValidationError("Failed to update account balances", IncomeErrorCodes.ACCOUNT_BALANCE_UPDATE_FAILED)
    
    async def create(self, income: IncomeCreate, user_id: int, workspace_id: UUID) -> IncomeOut:
        """Create a new income"""
        balance_updated = False
        try:
            # 1. Authorize workspace access (member role required for create)
            self.authorize_workspace_access(workspace_id, user_id, "member", "create_income")

            # Check subscription limits before creating (monthly limit)
            # Count only incomes created in the current calendar month
            current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current_count = self.db.query(Income).filter(
                Income.user_id == user_id,
                Income.workspace_id == workspace_id,
                Income.created_at >= current_month_start
            ).count()
            can_create, limit = self.subscription_client.check_limit(user_id, current_count, "incomes")
            if not can_create:
                raise IncomeLimitExceededError(current_count, limit or 0)

            # Validate amount
            if income.amount <= 0:
                raise IncomeAmountError("Income amount must be greater than 0", IncomeErrorCodes.INCOME_AMOUNT_NEGATIVE)

            if income.amount > 999999.99:
                raise IncomeAmountError("Income amount cannot exceed 999,999.99", IncomeErrorCodes.INCOME_AMOUNT_TOO_LARGE)

            # Validate description
            if income.description and len(income.description) > 500:
                raise IncomeDescriptionError("Description cannot exceed 500 characters", IncomeErrorCodes.INCOME_DESCRIPTION_TOO_LONG)

            # Validate category if provided
            if income.category_id:
                await self._validate_category(income.category_id, user_id, workspace_id)

            # Validate account if provided and update balance
            if income.account_id is not None:
                await self._validate_account(income.account_id, user_id, workspace_id)
                # Add amount to account balance with currency conversion
                await self.account_client.update_account_balance(income.account_id, user_id, income.amount, income.currency, workspace_id)
                balance_updated = True

            # Create income
            income_date = datetime.utcnow()
            if income.date:
                try:
                    income_date = datetime.fromisoformat(income.date)
                except ValueError:
                    raise IncomeDateError("Invalid date format. Use YYYY-MM-DD format", IncomeErrorCodes.INCOME_DATE_INVALID_FORMAT)
                if income_date.date() > datetime.utcnow().date():
                    raise IncomeDateError("Income date cannot be in the future", IncomeErrorCodes.INCOME_DATE_FUTURE)
            
            db_income = Income(
                user_id=user_id,
                workspace_id=workspace_id,
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
            # Compensate balance only if it was actually updated
            if balance_updated:
                try:
                    await self.account_client.update_account_balance(income.account_id, user_id, -income.amount, income.currency, workspace_id)
                    logger.warning(f"Compensated balance after failed income creation for account {income.account_id}")
                except Exception as comp_err:
                    logger.error(f"CRITICAL: Failed to compensate balance after failed create: {comp_err}")
            if isinstance(e, (IncomeAmountError, IncomeDateError, IncomeDescriptionError, IncomeValidationError, IncomeLimitExceededError, ExternalServiceError)):
                raise
            logger.error(f"Error creating income: {e}")
            raise IncomeValidationError("Failed to create income", IncomeErrorCodes.INCOME_VALIDATION_FAILED)

    def get_by_id(self, income_id: int, user_id: int, workspace_id: UUID) -> IncomeOut:
        """Get income by ID"""
        # 1. Authorize workspace access (viewer role required for read)
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_income")
        
        income = self.db.query(Income).filter(
            and_(Income.id == income_id, Income.workspace_id == workspace_id)
        ).first()
        
        if not income:
            raise IncomeNotFoundError(f"Income {income_id} not found")
        
        return IncomeOut.model_validate(income)
    
    def get_all(self, user_id: int, workspace_id: UUID, skip: int = 0, limit: int = 100) -> List[IncomeOut]:
        """Get all incomes in the workspace"""
        # 1. Authorize workspace access (viewer role required for read)
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "list_incomes")
        
        # 2. Filter by workspace
        incomes = self.db.query(Income).filter(
            Income.workspace_id == workspace_id
        ).order_by(desc(Income.date)).offset(skip).limit(limit).all()
        
        return [IncomeOut.model_validate(income) for income in incomes]
    
    def get_by_date_range(self, user_id: int, workspace_id: UUID, start_date: date, end_date: date) -> List[IncomeOut]:
        """Get incomes within a date range"""
        try:
            self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_incomes_by_date_range")

            if start_date > end_date:
                raise IncomeValidationError(
                    "Start date cannot be after end date",
                    IncomeErrorCodes.INCOME_VALIDATION_FAILED,
                )

            incomes = self.db.query(Income).filter(
                Income.workspace_id == workspace_id,
                Income.date >= start_date,
                Income.date <= end_date,
            ).order_by(desc(Income.date)).limit(5000).all()

            return [IncomeOut.model_validate(income) for income in incomes]
        except IncomeValidationError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving incomes by date range: {e}")
            raise IncomeValidationError(
                "Failed to retrieve incomes by date range",
                IncomeErrorCodes.INCOME_VALIDATION_FAILED,
            )

    def get_all_paginated(self, user_id: int, workspace_id: UUID, page: int = 1, size: int = 50) -> tuple[List[Income], int]:
        """Get paginated incomes for the user in the workspace"""
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "list_incomes_paginated")

        offset = (page - 1) * size

        total = self.db.query(Income).filter(Income.workspace_id == workspace_id).count()

        incomes = self.db.query(Income).filter(
            Income.workspace_id == workspace_id
        ).order_by(desc(Income.date)).offset(offset).limit(size).all()

        return incomes, total

    async def get_by_category(self, category_id: int, user_id: int, workspace_id: UUID = None) -> IncomesByCategoryResponse:
        """Get all incomes for a specific category with statistics"""
        filters = [Income.category_id == category_id, Income.user_id == user_id]
        if workspace_id is not None:
            self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_incomes_by_category")
            filters.append(Income.workspace_id == workspace_id)
        incomes = self.db.query(Income).filter(
            and_(*filters)
        ).order_by(desc(Income.date)).all()
        
        # Get user's base currency
        try:
            user_currency = self.currency_client.get_user_base_currency(user_id)
        except Exception as e:
            logger.warning(f"Could not fetch user currency for user {user_id}: {str(e)}, defaulting to USD")
            user_currency = settings.DEFAULT_CURRENCY

        # Fetch rates once for batch conversion
        rates = await self.currency_client.get_rates(user_currency)

        # Calculate statistics with currency conversion
        total_amount = 0.0
        count = 0

        for income in incomes:
            income_amount = float(income.amount)
            income_currency = income.currency or settings.DEFAULT_CURRENCY

            # Convert to user's currency if needed
            if income_currency != user_currency and rates:
                converted = self.currency_client.convert_with_rates(
                    income_amount, income_currency, user_currency, rates
                )
                if converted is not None:
                    income_amount = converted

            total_amount += income_amount
            count += 1
        
        # Calculate average
        average_amount = total_amount / count if count > 0 else 0.0
        
        # Create statistics
        statistics = CategoryIncomeStatistics(
            total_amount=round(total_amount, 2),
            count=count,
            average_amount=round(average_amount, 2),
            currency=user_currency
        )
        
        # Convert incomes to response format
        income_responses = [IncomeOut.model_validate(income) for income in incomes]
        
        return IncomesByCategoryResponse(
            incomes=income_responses,
            statistics=statistics
        )
    
    async def update(self, income_id: int, income_update: IncomeUpdate, user_id: int, workspace_id: UUID) -> IncomeOut:
        """Update income"""
        # 1. Authorize workspace access (member role required for update)
        self.authorize_workspace_access(workspace_id, user_id, "member", "update_income")
        
        db_income = self.db.query(Income).filter(
            and_(Income.id == income_id, Income.workspace_id == workspace_id)
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
                    raise IncomeAmountError("Income amount must be greater than 0", IncomeErrorCodes.INCOME_AMOUNT_NEGATIVE)
                if income_update.amount > 999999.99:
                    raise IncomeAmountError("Income amount cannot exceed 999,999.99", IncomeErrorCodes.INCOME_AMOUNT_TOO_LARGE)
                db_income.amount = round(income_update.amount, 2)
            
            if income_update.date is not None:
                try:
                    parsed_date = datetime.fromisoformat(income_update.date)
                except ValueError:
                    raise IncomeDateError("Invalid date format. Use YYYY-MM-DD format", IncomeErrorCodes.INCOME_DATE_INVALID_FORMAT)
                if parsed_date.date() > datetime.utcnow().date():
                    raise IncomeDateError("Income date cannot be in the future", IncomeErrorCodes.INCOME_DATE_FUTURE)
                db_income.date = parsed_date
            
            if income_update.description is not None:
                if len(income_update.description) > 500:
                    raise IncomeDescriptionError("Description cannot exceed 500 characters", IncomeErrorCodes.INCOME_DESCRIPTION_TOO_LONG)
                db_income.description = income_update.description
            
            if income_update.category_id is not None:
                # Validate category if provided
                if income_update.category_id > 0:
                    await self._validate_category(income_update.category_id, user_id, workspace_id)
                db_income.category_id = income_update.category_id
            
            if income_update.account_id is not None:
                # Validate account if provided
                if income_update.account_id > 0:
                    await self._validate_account(income_update.account_id, user_id, workspace_id)
                db_income.account_id = income_update.account_id

            # Handle account balance updates (before currency change, so old currency is used for restoration)
            await self._handle_balance_updates(db_income, old_amount, old_account_id, user_id, workspace_id)

            if income_update.currency is not None:
                db_income.currency = income_update.currency
            
            db_income.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(db_income)
            
            logger.info(f"Updated income {income_id} for user {user_id}")
            return IncomeOut.model_validate(db_income)
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, (IncomeAmountError, IncomeDateError, IncomeDescriptionError, IncomeValidationError)):
                raise
            logger.error(f"Error updating income: {e}")
            raise IncomeValidationError("Failed to update income", IncomeErrorCodes.INCOME_VALIDATION_FAILED)
    
    async def delete(self, income_id: int, user_id: int, workspace_id: UUID) -> bool:
        """Delete income"""
        # 1. Authorize workspace access (member role required for delete)
        self.authorize_workspace_access(workspace_id, user_id, "member", "delete_income")
        
        db_income = self.db.query(Income).filter(
            and_(Income.id == income_id, Income.workspace_id == workspace_id)
        ).first()
        
        if not db_income:
            raise IncomeNotFoundError(f"Income {income_id} not found")
        
        # Restore balance to account if income had one (subtract the amount)
        if db_income.account_id is not None:
            await self.account_client.update_account_balance(db_income.account_id, user_id, -db_income.amount, db_income.currency, workspace_id)
            logger.info(f"Restored {db_income.amount} {db_income.currency} from account {db_income.account_id} after income deletion")

        try:
            self.db.delete(db_income)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            # Compensate: reverse the balance change
            if db_income.account_id is not None:
                try:
                    await self.account_client.update_account_balance(db_income.account_id, user_id, db_income.amount, db_income.currency, workspace_id)
                    logger.warning(f"Compensated balance after failed delete for income {income_id}")
                except Exception as comp_err:
                    logger.error(f"CRITICAL: Failed to compensate balance after failed delete: {comp_err}")
            raise IncomeValidationError("Failed to delete income", IncomeErrorCodes.INCOME_VALIDATION_FAILED)

        logger.info(f"Deleted income {income_id} for user {user_id}")
        return True
    
    def get_summary(self, user_id: int, workspace_id: UUID, start_date: datetime, end_date: datetime) -> IncomeSummary:
        """Get income summary for date range"""
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_income_summary")
        incomes = self.db.query(Income).filter(
            and_(
                Income.user_id == user_id,
                Income.workspace_id == workspace_id,
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
    
    def get_stats(self, user_id: int, workspace_id: UUID) -> IncomeStats:
        """Get income statistics for user in workspace"""
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_income_stats")
        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        base_filter = and_(Income.user_id == user_id, Income.workspace_id == workspace_id)

        # Total income
        total_income = self.db.query(func.sum(Income.amount)).filter(
            base_filter
        ).scalar() or 0

        # Monthly income
        monthly_income = self.db.query(func.sum(Income.amount)).filter(
            and_(base_filter, Income.date >= current_month_start)
        ).scalar() or 0

        # Yearly income
        yearly_income = self.db.query(func.sum(Income.amount)).filter(
            and_(base_filter, Income.date >= current_year_start)
        ).scalar() or 0

        # Count and average
        income_count = self.db.query(func.count(Income.id)).filter(
            base_filter
        ).scalar() or 0

        average_income = total_income / income_count if income_count > 0 else 0

        return IncomeStats(
            total_income=total_income,
            monthly_income=monthly_income,
            yearly_income=yearly_income,
            income_count=income_count,
            average_income=average_income
        )

    def get_current_month_count(self, user_id: int, workspace_id: UUID) -> dict:
        """Get current month income count and limit"""
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_current_month_count")
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count = self.db.query(Income).filter(
            and_(
                Income.user_id == user_id,
                Income.workspace_id == workspace_id,
                Income.created_at >= current_month_start
            )
        ).count()

        features = self.subscription_client.get_user_features(user_id) or {}
        income_feature = features.get("incomes", {})
        limit = income_feature.get("limit_value")

        return {"count": count, "limit": limit}
