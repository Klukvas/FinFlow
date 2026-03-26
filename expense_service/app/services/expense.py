from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, CategoryExpenseStatistics, ExpensesByCategoryResponse
from app.clients.category_service_client import CategoryServiceClient
from app.clients.account_service_client import AccountServiceClient
from shared.clients import CurrencyServiceClient
from shared.clients import UserServiceClient
from shared.clients import SubscriptionClient
from shared.auth import WorkspaceAuthorizationMixin
from app.exceptions import (
    ErrorCode,
    ExpenseNotFoundError,
    ExpenseValidationError,
    ExpenseAmountError,
    ExpenseDateError,
    ExpenseDescriptionError,
    ExternalServiceError,
    ExpenseLimitExceededError
)
from app.utils.logger import get_logger, log_operation, log_security_event
from app.config import settings

class ExpenseService(WorkspaceAuthorizationMixin):
    def __init__(self, db: Session, category_client: CategoryServiceClient, account_client: AccountServiceClient):
        super().__init__(
            access_denied_error=lambda msg: ExpenseValidationError(msg, ErrorCode.EXPENSE_VALIDATION_FAILED),
            workspace_mismatch_error=lambda msg: ExpenseValidationError(msg, ErrorCode.EXPENSE_VALIDATION_FAILED),
        )
        self.db = db
        self.category_client = category_client
        self.account_client = account_client
        self.currency_client = CurrencyServiceClient.get_instance()
        self.user_client = UserServiceClient.get_instance()
        self.logger = get_logger(__name__)
        self.subscription_client = SubscriptionClient.get_instance()

    def _validate_expense_ownership(self, expense_id: int, user_id: int, workspace_id: UUID) -> Expense:
        """Validate that expense exists and belongs to user and workspace"""
        expense = self.db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == user_id,
            Expense.workspace_id == workspace_id
        ).first()
        if not expense:
            raise ExpenseNotFoundError(expense_id)
        return expense

    def _validate_amount(self, amount: Decimal) -> Decimal:
        """Validate and normalize amount"""
        if amount <= 0:
            raise ExpenseValidationError(
                "Amount must be greater than 0",
                ErrorCode.EXPENSE_AMOUNT_INVALID,
                {"amount": float(amount)}
            )
        
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
            raise ExpenseDateError(str(expense_date), "future")
        
        # Check if date is not too far in the past (e.g., more than 10 years)
        min_date = date.today().replace(year=date.today().year - 10)
        if expense_date < min_date:
            raise ExpenseDateError(str(expense_date), "too_old")
        
        return expense_date

    def _validate_category(self, category_id: Optional[int], user_id: int, workspace_id: UUID) -> dict:
        """Validate category exists and belongs to user in the workspace"""
        try:
            return self.category_client.validate_category(category_id, user_id, workspace_id)
        except Exception as e:
            self.logger.error(f"Category validation failed: {e}")
            raise ExternalServiceError("category_service", str(e), ErrorCode.CATEGORY_VALIDATION_FAILED)

    def _validate_account(self, account_id: int, user_id: int, workspace_id: UUID = None) -> dict:
        """Validate account exists and belongs to user"""
        try:
            return self.account_client.validate_account(account_id, user_id, workspace_id)
        except Exception as e:
            self.logger.error(f"Account validation failed: {e}")
            raise ExternalServiceError("account_service", str(e), ErrorCode.ACCOUNT_VALIDATION_FAILED)

    def _handle_balance_updates(self, expense: Expense, old_amount: float, old_account_id: int, user_id: int, workspace_id: UUID = None) -> None:
        """Handle account balance updates when expense amount or account changes"""
        try:
            # If account changed or amount changed, we need to update balances
            if expense.account_id != old_account_id or expense.amount != old_amount:

                # Restore balance to old account if it had one
                if old_account_id is not None:
                    # Get old account currency and convert if needed
                    old_account_data = self.account_client.validate_account(old_account_id, user_id, workspace_id)
                    old_account_currency = old_account_data.get("account", {}).get("currency", settings.DEFAULT_CURRENCY)

                    # Convert expense amount to account currency if needed
                    amount_to_restore = float(old_amount)
                    if expense.currency != old_account_currency:
                        converted_amount = self.currency_client.convert_amount(
                            float(old_amount), expense.currency, old_account_currency
                        )
                        if converted_amount is not None:
                            amount_to_restore = converted_amount

                    self.account_client.update_account_balance(
                        old_account_id, user_id, amount_to_restore, old_account_currency, workspace_id
                    )
                    self.logger.info(f"Restored {amount_to_restore} {old_account_currency} to account {old_account_id}")

                # Deduct from new account if it has one
                if expense.account_id is not None:
                    # Get account currency and convert expense amount if needed
                    account_data = self.account_client.validate_account(expense.account_id, user_id, workspace_id)
                    account_currency = account_data.get("account", {}).get("currency", settings.DEFAULT_CURRENCY)

                    # Convert expense amount to account currency if needed
                    amount_to_deduct = float(expense.amount)
                    if expense.currency != account_currency:
                        converted_amount = self.currency_client.convert_amount(
                            float(expense.amount), expense.currency, account_currency
                        )
                        if converted_amount is not None:
                            amount_to_deduct = converted_amount

                    self.account_client.update_account_balance(
                        expense.account_id, user_id, -amount_to_deduct, account_currency, workspace_id
                    )
                    self.logger.info(f"Deducted {amount_to_deduct} {account_currency} from account {expense.account_id}")
                    
        except Exception as e:
            self.logger.error(f"Failed to handle balance updates: {e}")
            raise ExpenseValidationError(
                "Failed to update account balances",
                ErrorCode.ACCOUNT_BALANCE_UPDATE_FAILED,
                {"original_error": str(e)}
            )

    def create(self, data: ExpenseCreate, user_id: int, workspace_id: UUID) -> Expense:
        """Create a new expense with proper validation and transaction management"""
        try:
            # 1. Authorize workspace access (member role required for create)
            self.authorize_workspace_access(workspace_id, user_id, "member", "create_expense")
            
            # Check subscription limits before creating (monthly limit)
            # Count only expenses created in the current calendar month
            current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current_count = self.db.query(Expense).filter(
                Expense.user_id == user_id,
                Expense.workspace_id == workspace_id,
                Expense.created_at >= current_month_start
            ).count()
            can_create, limit = self.subscription_client.check_limit(user_id, current_count, "expenses")
            if not can_create:
                raise ExpenseLimitExceededError(current_count, limit or 0)
            
            # Validate amount
            validated_amount = self._validate_amount(data.amount)
            
            # Validate description
            validated_description = self._validate_description(data.description)
            
            # Validate date
            validated_date = self._validate_date(data.date)
            
            # Validate category only if provided and valid
            self.logger.info(f"Category ID received: {data.category_id} (type: {type(data.category_id)})")
            if data.category_id is not None and data.category_id > 0:
                self.logger.info(f"Validating category: {data.category_id}")
                self._validate_category(data.category_id, user_id, workspace_id)
            else:
                self.logger.info("Skipping category validation - category_id is None, 0, or invalid")
            
            # Validate account if provided and update balance with currency conversion
            if data.account_id is not None:
                account_data = self._validate_account(data.account_id, user_id, workspace_id)
                account_currency = account_data.get("account", {}).get("currency", settings.DEFAULT_CURRENCY)
                expense_currency = data.currency or settings.DEFAULT_CURRENCY
                
                # Convert amount if currencies differ
                amount_to_deduct = validated_amount
                if expense_currency != account_currency:
                    self.logger.info(f"Converting expense from {expense_currency} to account currency {account_currency}")
                    converted_amount = self.currency_client.convert_amount(
                        float(validated_amount), 
                        expense_currency, 
                        account_currency
                    )
                    if converted_amount is not None:
                        amount_to_deduct = Decimal(str(converted_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        self.logger.info(f"Converted {validated_amount} {expense_currency} to {amount_to_deduct} {account_currency}")
                    else:
                        self.logger.warning(f"Currency conversion failed, using original amount")
                
                # Deduct amount from account balance with currency conversion
                self.account_client.update_account_balance(
                    data.account_id,
                    user_id,
                    -float(amount_to_deduct),
                    account_currency,
                    workspace_id
                )
            
            # Log currency value for debugging
            self.logger.info(f"Currency value: {data.currency} (type: {type(data.currency)})")
            
            expense = Expense(
                amount=validated_amount,
                description=validated_description,
                category_id=data.category_id if data.category_id and data.category_id > 0 else None,
                account_id=data.account_id,
                currency=data.currency or settings.DEFAULT_CURRENCY,  # Default to configured currency if None
                date=validated_date,
                user_id=user_id,
                workspace_id=workspace_id
            )

            try:
                self.db.add(expense)
                self.db.commit()
                self.db.refresh(expense)
                log_operation(self.logger, "Expense created", user_id, f"ID: {expense.id}, Amount: {validated_amount}, Category: {data.category_id}, Account: {data.account_id}, Date: {validated_date}")
                return expense
            except Exception as e:
                self.db.rollback()
                self.logger.error(f"Database error during expense creation: {e}")
                raise ExpenseValidationError(
                    "Failed to create expense",
                    ErrorCode.EXPENSE_CREATION_FAILED,
                    {"original_error": str(e)}
                )
            
            
        except (ExpenseValidationError, ExpenseAmountError, ExpenseDateError,
                ExpenseDescriptionError, ExpenseLimitExceededError, ExternalServiceError):
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Database integrity error during expense creation: {e}")
            raise ExpenseValidationError(
                "Database constraint violation",
                ErrorCode.DATABASE_CONSTRAINT_VIOLATION,
                {"original_error": str(e)}
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error during expense creation: {e}")
            raise ExpenseValidationError(
                "Failed to create expense",
                ErrorCode.EXPENSE_CREATION_FAILED,
                {"original_error": str(e)}
            )

    def get_all(self, user_id: int, workspace_id: UUID) -> List[Expense]:
        """Get all expenses for the user in the workspace"""
        try:
            # 1. Authorize workspace access (viewer role required for read)
            self.authorize_workspace_access(workspace_id, user_id, "viewer", "list_expenses")

            # 2. Filter by workspace
            return self.db.query(Expense).filter(
                Expense.workspace_id == workspace_id
            ).order_by(Expense.date.desc()).all()
        except (ExpenseValidationError, ExternalServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving expenses: {e}")
            raise ExpenseValidationError(
                "Failed to retrieve expenses",
                ErrorCode.EXPENSE_RETRIEVAL_FAILED,
                {"original_error": str(e)}
            )

    def get_all_paginated(self, user_id: int, workspace_id: UUID, page: int = 1, size: int = 50) -> tuple[List[Expense], int]:
        """Get paginated expenses for the user in the workspace"""
        try:
            # 1. Authorize workspace access (viewer role required for read)
            self.authorize_workspace_access(workspace_id, user_id, "viewer", "list_expenses_paginated")

            # Calculate offset
            offset = (page - 1) * size

            # 2. Get total count filtered by workspace
            total = self.db.query(Expense).filter(Expense.workspace_id == workspace_id).count()

            # 3. Get paginated results filtered by workspace
            expenses = self.db.query(Expense).filter(
                Expense.workspace_id == workspace_id
            ).order_by(Expense.date.desc()).offset(offset).limit(size).all()

            return expenses, total
        except (ExpenseValidationError, ExternalServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving paginated expenses: {e}")
            raise ExpenseValidationError(
                "Failed to retrieve expenses",
                ErrorCode.EXPENSE_RETRIEVAL_FAILED,
                {"original_error": str(e)}
            )

    def get(self, expense_id: int, user_id: int, workspace_id: UUID) -> Expense:
        """Get a specific expense by ID"""
        # 1. Authorize workspace access (viewer role required for read)
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_expense")
        
        # 2. Get and validate expense belongs to workspace
        return self._validate_expense_ownership(expense_id, user_id, workspace_id)

    def update(self, expense_id: int, data: ExpenseUpdate, user_id: int, workspace_id: UUID) -> Expense:
        """Update an existing expense with proper validation and transaction management"""
        try:
            # 1. Authorize workspace access (member role required for update)
            self.authorize_workspace_access(workspace_id, user_id, "member", "update_expense")
            
            # 2. Get and validate expense belongs to workspace
            expense = self._validate_expense_ownership(expense_id, user_id, workspace_id)
            
            # Track changes for logging
            changes = []
            
            # Store original values for balance calculations
            old_amount = expense.amount
            old_account_id = expense.account_id
            
            # Validate and update amount if provided
            if data.amount is not None:
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
            
            # Validate and update category if provided and valid
            if data.category_id is not None and data.category_id > 0:
                old_category = expense.category_id
                self._validate_category(data.category_id, user_id, workspace_id)
                expense.category_id = data.category_id
                changes.append(f"Category: {old_category} -> {data.category_id}")
            elif data.category_id is not None and data.category_id == 0:
                # Set category to None if 0 is provided
                old_category = expense.category_id
                expense.category_id = None
                changes.append(f"Category: {old_category} -> None")
            
            # Validate and update account if provided
            if data.account_id is not None:
                old_account = expense.account_id
                self._validate_account(data.account_id, user_id, workspace_id)
                expense.account_id = data.account_id
                changes.append(f"Account: {old_account} -> {data.account_id}")
            
            # Handle account balance updates BEFORE currency mutation (uses old currency for restoration)
            self._handle_balance_updates(expense, old_amount, old_account_id, user_id, workspace_id)

            # Validate and update currency if provided (AFTER balance updates)
            if data.currency is not None:
                old_currency = expense.currency
                expense.currency = data.currency
                changes.append(f"Currency: {old_currency} -> {data.currency}")
            
            self.db.commit()
            self.db.refresh(expense)
            
            log_operation(
                self.logger,
                "Expense updated",
                user_id,
                f"Expense ID: {expense_id}, Changes: {', '.join(changes) if changes else 'No changes'}"
            )
            
            return expense
            
        except (ExpenseNotFoundError, ExpenseValidationError, ExpenseAmountError, 
                ExpenseDateError, ExpenseDescriptionError, ExternalServiceError):
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Database integrity error during expense update: {e}")
            raise ExpenseValidationError(
                "Database constraint violation",
                ErrorCode.DATABASE_CONSTRAINT_VIOLATION,
                {"original_error": str(e)}
            )
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error during expense update: {e}")
            raise ExpenseValidationError(
                "Failed to update expense",
                ErrorCode.EXPENSE_UPDATE_FAILED,
                {"original_error": str(e)}
            )

    def delete(self, expense_id: int, user_id: int, workspace_id: UUID) -> dict:
        """Delete an expense with proper validation and transaction management"""
        try:
            # 1. Authorize workspace access (member role required for delete)
            self.authorize_workspace_access(workspace_id, user_id, "member", "delete_expense")
            
            # 2. Get and validate expense belongs to workspace
            expense = self._validate_expense_ownership(expense_id, user_id, workspace_id)
            
            amount = expense.amount
            category_id = expense.category_id
            account_id = expense.account_id
            expense_date = expense.date
            
            # Restore balance to account if expense had one
            if account_id is not None:
                self.account_client.update_account_balance(account_id, user_id, amount, expense.currency, workspace_id)
                self.logger.info(f"Restored {amount} {expense.currency} to account {account_id} after expense deletion")
            
            self.db.delete(expense)
            self.db.commit()
            
            log_operation(
                self.logger,
                "Expense deleted",
                user_id,
                f"Expense ID: {expense_id}, Amount: {amount}, Category: {category_id}, Account: {account_id}, Date: {expense_date}"
            )
            
            return {"detail": "Expense deleted successfully"}
            
        except (ExpenseNotFoundError, ExpenseValidationError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error during expense deletion: {e}")
            raise ExpenseValidationError(
                "Failed to delete expense",
                ErrorCode.EXPENSE_DELETE_FAILED,
                {"original_error": str(e)}
            )

    def get_by_category(self, category_id: int, user_id: int, workspace_id: UUID) -> ExpensesByCategoryResponse:
        """Get all expenses for a specific category with statistics"""
        try:
            # 1. Authorize workspace access (viewer role required for read)
            self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_expenses_by_category")
            
            # 2. Validate the category belongs to the user in the workspace
            self._validate_category(category_id, user_id, workspace_id)
            
            # 3. Get all expenses for this category filtered by workspace
            expenses = self.db.query(Expense).filter(
                Expense.workspace_id == workspace_id,
                Expense.category_id == category_id
            ).order_by(Expense.date.desc()).all()
            
            # Get user's base currency
            try:
                user_currency = self.user_client.get_user_base_currency(user_id)
            except Exception as e:
                self.logger.warning(f"Could not fetch user currency for user {user_id}: {str(e)}, defaulting to USD")
                user_currency = settings.DEFAULT_CURRENCY

            # Fetch rates once for batch conversion
            rates = self.currency_client.get_rates(user_currency)

            # Calculate statistics with currency conversion
            total_amount = 0.0
            count = 0

            for expense in expenses:
                expense_amount = float(expense.amount)
                expense_currency = expense.currency or settings.DEFAULT_CURRENCY

                # Convert to user's currency if needed
                if expense_currency != user_currency and rates:
                    converted = CurrencyServiceClient.convert_with_rates(
                        expense_amount, expense_currency, user_currency, rates
                    )
                    if converted is not None:
                        expense_amount = converted

                total_amount += expense_amount
                count += 1
            
            # Calculate average
            average_amount = total_amount / count if count > 0 else 0.0
            
            # Create statistics
            statistics = CategoryExpenseStatistics(
                total_amount=round(total_amount, 2),
                count=count,
                average_amount=round(average_amount, 2),
                currency=user_currency
            )
            
            # Convert expenses to response format
            from app.schemas.expense import ExpenseResponse
            expense_responses = [ExpenseResponse.model_validate(expense) for expense in expenses]
            
            return ExpensesByCategoryResponse(
                expenses=expense_responses,
                statistics=statistics
            )
        except (ExpenseValidationError, ExternalServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving expenses by category: {e}")
            raise ExpenseValidationError(
                "Failed to retrieve expenses by category",
                ErrorCode.EXPENSE_RETRIEVAL_FAILED,
                {"original_error": str(e), "category_id": category_id}
            )

    def get_by_date_range(self, start_date: date, end_date: date, user_id: int, workspace_id: UUID) -> List[Expense]:
        """Get expenses within a date range"""
        try:
            # 1. Authorize workspace access (viewer role required for read)
            self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_expenses_by_date_range")
            
            if start_date > end_date:
                raise ExpenseValidationError(
                    "Start date cannot be after end date",
                    ErrorCode.INVALID_DATE_RANGE,
                    {"start_date": str(start_date), "end_date": str(end_date)}
                )
            
            # 2. Filter by workspace
            return self.db.query(Expense).filter(
                Expense.workspace_id == workspace_id,
                Expense.date >= start_date,
                Expense.date <= end_date
            ).order_by(Expense.date.desc()).all()
        except (ExpenseValidationError, ExternalServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving expenses by date range: {e}")
            raise ExpenseValidationError(
                "Failed to retrieve expenses by date range",
                ErrorCode.EXPENSE_RETRIEVAL_FAILED,
                {"original_error": str(e), "start_date": str(start_date), "end_date": str(end_date)}
            )

    def get_current_month_count(self, user_id: int, workspace_id: UUID) -> dict:
        """Get current month expense count and limit"""
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_current_month_count")
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        count = self.db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.workspace_id == workspace_id,
            Expense.created_at >= current_month_start
        ).count()

        features = self.subscription_client.get_user_features(user_id) or {}
        expense_feature = features.get("expenses", {})
        limit = expense_feature.get("limit_value")

        return {"count": count, "limit": limit}