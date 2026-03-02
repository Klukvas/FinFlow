from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate, AccountSummary, AccountTransaction, AccountTransactionSummary
from app.exceptions import (
    AccountNotFoundError,
    AccountValidationError,
    AccountOwnershipError,
    AccountArchivedError,
    AccountBalanceError,
    AccountLimitExceededError,
    AccountReadOnlyExcessError,
    AccountErrorCode
)
from app.utils.logger import get_logger, log_operation
from app.utils.validation import validate_currency_code, validate_balance, validate_account_name, validate_account_description, sanitize_input
from app.clients.expense_service_client import ExpenseServiceClient
from app.clients.income_service_client import IncomeServiceClient
from shared.clients import CurrencyServiceClient
from shared.clients import SubscriptionClient
from shared.clients import UserServiceClient
from shared.auth import WorkspaceAuthorizationMixin
from app.schemas.account import AccountStatisticsResponse
from app.config import settings

class AccountService(WorkspaceAuthorizationMixin):
    def __init__(self, db: Session, expense_client: ExpenseServiceClient = None, income_client: IncomeServiceClient = None, currency_client: CurrencyServiceClient = None):
        super().__init__(
            access_denied_error=lambda msg: AccountValidationError(msg, AccountErrorCode.ACCOUNT_NOT_OWNED),
            workspace_mismatch_error=lambda msg: AccountValidationError(msg, AccountErrorCode.ACCOUNT_NOT_OWNED),
        )
        self.db = db
        self.logger = get_logger(__name__)
        self.expense_client = expense_client or ExpenseServiceClient()
        self.income_client = income_client or IncomeServiceClient()
        self.currency_client = currency_client or CurrencyServiceClient.get_instance()
        self.subscription_client = SubscriptionClient.get_instance()
        self.user_client = UserServiceClient.get_instance()

    def create_account(self, account_data: AccountCreate, user_id: int, workspace_id: UUID) -> Account:
        """Create a new account for a user in a workspace"""
        try:
            # 1. Authorize workspace access (member role required for create)
            self.authorize_workspace_access(workspace_id, user_id, "member", "create_account")
            
            # Check subscription limits before creating
            current_count = self.db.query(Account).filter(
                Account.owner_id == user_id,
                Account.workspace_id == workspace_id
            ).count()
            can_create, limit = self.subscription_client.check_limit(user_id, current_count, "accounts")
            if not can_create:
                raise AccountLimitExceededError(current_count, limit or 0)
            
            # Validate input
            if not validate_account_name(account_data.name):
                raise AccountValidationError("Invalid account name", AccountErrorCode.INVALID_ACCOUNT_NAME)
            
            if not validate_currency_code(account_data.currency):
                raise AccountValidationError("Invalid currency code", AccountErrorCode.INVALID_CURRENCY)
            
            if not validate_balance(account_data.balance):
                raise AccountValidationError("Invalid balance amount", AccountErrorCode.INVALID_BALANCE)
            
            if not validate_account_description(account_data.description):
                raise AccountValidationError("Invalid description length", AccountErrorCode.INVALID_ACCOUNT_DESCRIPTION)

            # Create account
            account = Account(
                name=sanitize_input(account_data.name),
                type=account_data.type,
                currency=account_data.currency.upper(),
                balance=account_data.balance,
                description=sanitize_input(account_data.description) if account_data.description else None,
                owner_id=user_id,
                workspace_id=workspace_id
            )
            
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
            
            log_operation(
                self.logger,
                "CREATE_ACCOUNT",
                user_id,
                f"Account ID: {account.id}, Name: {account.name}, Type: {account.type.value}, Currency: {account.currency}"
            )
            
            return account
            
        except IntegrityError as e:
            self.db.rollback()
            self.logger.error(f"Database integrity error creating account: {e}")
            raise AccountValidationError("Account creation failed due to data constraints", AccountErrorCode.DATABASE_ERROR)
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error creating account: {e}")
            raise AccountValidationError(f"Failed to create account: {str(e)}", AccountErrorCode.UNKNOWN_ERROR)

    def get_account(self, account_id: int, user_id: int, workspace_id: UUID) -> Account:
        """Get a specific account by ID in the workspace"""
        # 1. Authorize workspace access (viewer role required for read)
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_account")
        
        # 2. Get account filtered by workspace
        account = self.db.query(Account).filter(
            Account.id == account_id,
            Account.workspace_id == workspace_id
        ).first()
        
        if not account:
            raise AccountNotFoundError(account_id)
        
        return account

    def get_user_accounts(self, user_id: int, workspace_id: UUID, include_archived: bool = False) -> List[Account]:
        """Get all accounts in the workspace"""
        # 1. Authorize workspace access (viewer role required for read)
        self.authorize_workspace_access(workspace_id, user_id, "viewer", "list_accounts")
        
        # 2. Filter by workspace
        query = self.db.query(Account).filter(Account.workspace_id == workspace_id)
        
        if not include_archived:
            query = query.filter(Account.is_archived == False)
        
        return query.order_by(Account.created_at.desc()).all()

    def _get_ordered_ids(self, workspace_id: UUID) -> list:
        rows = self.db.query(Account.id).filter(
            Account.workspace_id == workspace_id
        ).order_by(Account.created_at.asc(), Account.id.asc()).all()
        return [row[0] for row in rows]

    def _check_modify_allowed(self, record_id: int, user_id: int, workspace_id: UUID):
        ordered_ids = self._get_ordered_ids(workspace_id)
        if not self.subscription_client.check_modify_allowed(user_id, record_id, "accounts", ordered_ids):
            features = self.subscription_client.get_user_features(user_id) or {}
            limit = features.get("accounts", {}).get("limit_value", 0)
            raise AccountReadOnlyExcessError(record_id, len(ordered_ids), limit)

    def update_account(self, account_id: int, account_data: AccountUpdate, user_id: int, workspace_id: UUID) -> Account:
        """Update an existing account"""
        # 1. Authorize workspace access (member role required for update)
        self.authorize_workspace_access(workspace_id, user_id, "member", "update_account")
        
        account = self.get_account(account_id, user_id, workspace_id)
        
        if account.is_archived:
            raise AccountArchivedError(account_id)

        self._check_modify_allowed(account_id, user_id, workspace_id)

        # Validate updates
        if account_data.name is not None and not validate_account_name(account_data.name):
            raise AccountValidationError("Invalid account name", AccountErrorCode.INVALID_ACCOUNT_NAME)
        
        if account_data.currency is not None and not validate_currency_code(account_data.currency):
            raise AccountValidationError("Invalid currency code", AccountErrorCode.INVALID_CURRENCY)
        
        if account_data.balance is not None and not validate_balance(account_data.balance):
            raise AccountValidationError("Invalid balance amount", AccountErrorCode.INVALID_BALANCE)
        
        if account_data.description is not None and not validate_account_description(account_data.description):
            raise AccountValidationError("Invalid description length", AccountErrorCode.INVALID_ACCOUNT_DESCRIPTION)

        try:
            # Update fields
            if account_data.name is not None:
                account.name = sanitize_input(account_data.name)
            if account_data.type is not None:
                account.type = account_data.type
            if account_data.currency is not None:
                account.currency = account_data.currency.upper()
            if account_data.balance is not None:
                account.balance = account_data.balance
            if account_data.description is not None:
                account.description = sanitize_input(account_data.description) if account_data.description else None
            if account_data.is_active is not None:
                account.is_active = account_data.is_active
            
            account.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(account)
            
            log_operation(
                self.logger,
                "UPDATE_ACCOUNT",
                user_id,
                f"Account ID: {account.id}, Name: {account.name}, Type: {account.type.value}"
            )
            
            return account
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error updating account: {e}")
            raise AccountValidationError(f"Failed to update account: {str(e)}", AccountErrorCode.UNKNOWN_ERROR)

    def archive_account(self, account_id: int, user_id: int, workspace_id: UUID) -> Account:
        """Archive an account (soft delete)"""
        # 1. Authorize workspace access (member role required)
        self.authorize_workspace_access(workspace_id, user_id, "member", "archive_account")
        
        account = self.get_account(account_id, user_id, workspace_id)
        
        if account.is_archived:
            raise AccountArchivedError(account_id)
        
        try:
            account.is_archived = True
            account.is_active = False
            account.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(account)
            
            log_operation(
                self.logger,
                "ARCHIVE_ACCOUNT",
                user_id,
                f"Account ID: {account.id}, Name: {account.name}"
            )
            
            return account
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error archiving account: {e}")
            raise AccountValidationError(f"Failed to archive account: {str(e)}", AccountErrorCode.UNKNOWN_ERROR)

    def update_balance(self, account_id: int, new_balance: float, user_id: int, workspace_id: UUID) -> Account:
        """Update account balance"""
        # 1. Authorize workspace access (member role required)
        self.authorize_workspace_access(workspace_id, user_id, "member", "update_balance")
        
        account = self.get_account(account_id, user_id, workspace_id)
        
        if account.is_archived:
            raise AccountArchivedError(account_id)
        
        if not validate_balance(new_balance):
            raise AccountBalanceError("Invalid balance amount", AccountErrorCode.INVALID_BALANCE)
        
        try:
            old_balance = account.balance
            account.balance = new_balance
            account.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(account)
            
            log_operation(
                self.logger,
                "UPDATE_BALANCE",
                user_id,
                f"Account ID: {account.id}, Old Balance: {old_balance}, New Balance: {new_balance}"
            )
            
            return account
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error updating balance: {e}")
            raise AccountBalanceError(f"Failed to update balance: {str(e)}", AccountErrorCode.UNKNOWN_ERROR)

    async def update_balance_with_conversion(
        self,
        account_id: int,
        amount_change: float,
        transaction_currency: str,
        user_id: int,
        workspace_id: UUID = None
    ) -> Account:
        """
        Update account balance with automatic currency conversion.

        Args:
            account_id: ID of the account to update
            amount_change: Amount to add (positive) or subtract (negative)
            transaction_currency: Currency of the transaction
            user_id: ID of the user (for ownership validation)
            workspace_id: Workspace ID for isolation

        Returns:
            Updated account
        """
        if workspace_id is not None:
            account = self.get_account(account_id, user_id, workspace_id)
        else:
            # Fallback: lookup account without workspace filter (for backwards compat)
            account = self.db.query(Account).filter(
                Account.id == account_id,
                Account.owner_id == user_id
            ).first()
            if not account:
                from app.exceptions import AccountNotFoundError
                raise AccountNotFoundError(account_id)
        
        if account.is_archived:
            raise AccountArchivedError(account_id)
        
        if not validate_balance(abs(amount_change)):
            raise AccountBalanceError("Invalid amount", AccountErrorCode.INVALID_BALANCE)
        
        try:
            # If currencies are the same, no conversion needed
            actual_workspace_id = workspace_id or account.workspace_id
            if transaction_currency.upper() == account.currency.upper():
                new_balance = account.balance + amount_change
                if new_balance < 0:
                    raise AccountBalanceError("Insufficient funds in account", AccountErrorCode.INSUFFICIENT_FUNDS)

                return self.update_balance(account_id, new_balance, user_id, actual_workspace_id)
            
            # Convert amount to account currency (always use positive amount for conversion)
            converted_amount = await self.currency_client.convert_amount(
                abs(amount_change), 
                transaction_currency.upper(), 
                account.currency.upper()
            )
            
            if converted_amount is None:
                self.logger.error(f"Failed to convert {amount_change} {transaction_currency} to {account.currency}")
                raise AccountBalanceError(f"Currency conversion failed: {transaction_currency} to {account.currency}", AccountErrorCode.CURRENCY_CONVERSION_FAILED)
            
            # Restore the original sign after conversion
            final_amount = converted_amount if amount_change >= 0 else -converted_amount
            new_balance = account.balance + final_amount
            if new_balance < 0:
                raise AccountBalanceError("Insufficient funds in account", AccountErrorCode.INSUFFICIENT_FUNDS)
            
            self.logger.info(
                f"Converted {amount_change} {transaction_currency} to {final_amount} {account.currency} "
                f"for account {account_id}"
            )
            
            return self.update_balance(account_id, new_balance, user_id, actual_workspace_id)

        except AccountBalanceError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in balance update with conversion: {e}")
            raise AccountBalanceError(f"Failed to update balance with conversion: {str(e)}", AccountErrorCode.UNKNOWN_ERROR)

    def get_account_summary(self, account_id: int, user_id: int, workspace_id: UUID) -> AccountSummary:
        """Get account summary with transaction counts"""
        account = self.get_account(account_id, user_id, workspace_id)
        
        # Get transaction counts from external services
        try:
            expenses = self.expense_client.get_expenses_by_account(account_id, user_id, limit=1)
            incomes = self.income_client.get_incomes_by_account(account_id, user_id, limit=1)
            
            transaction_count = len(expenses) + len(incomes)
            last_transaction_date = None
            
            # Get the most recent transaction date
            all_transactions = []
            if expenses:
                all_transactions.extend([(exp.get('date'), 'expense') for exp in expenses if exp.get('date')])
            if incomes:
                all_transactions.extend([(inc.get('date'), 'income') for inc in incomes if inc.get('date')])
            
            if all_transactions:
                # Sort by date and get the most recent
                all_transactions.sort(key=lambda x: x[0] or '', reverse=True)
                last_transaction_date = all_transactions[0][0]
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch transaction data: {e}")
            transaction_count = 0
            last_transaction_date = None
        
        return AccountSummary(
            id=account.id,
            name=account.name,
            type=account.type,
            currency=account.currency,
            balance=account.balance,
            is_active=account.is_active,
            transaction_count=transaction_count,
            last_transaction_date=last_transaction_date
        )

    def get_account_transactions(self, account_id: int, user_id: int, workspace_id: UUID, limit: int = 100, offset: int = 0) -> AccountTransactionSummary:
        """Get account transactions from both expense and income services"""
        account = self.get_account(account_id, user_id, workspace_id)
        
        try:
            # Fetch transactions from both services
            expenses_data = self.expense_client.get_expenses_by_account(account_id, user_id, limit, offset)
            incomes_data = self.income_client.get_incomes_by_account(account_id, user_id, limit, offset)
            
            # Convert to transaction objects
            transactions = []
            total_income = 0.0
            total_expenses = 0.0
            
            for expense in expenses_data:
                expense_id = expense.get('id')
                expense_amount = expense.get('amount')
                expense_date = expense.get('date')
                if expense_id is None or expense_amount is None or expense_date is None:
                    self.logger.warning(f"Skipping incomplete expense record: {expense}")
                    continue
                transactions.append(AccountTransaction(
                    id=expense_id,
                    amount=-expense_amount,  # Expenses are negative
                    description=expense.get('description'),
                    date=expense_date,
                    type='expense',
                    category_id=expense.get('category_id'),
                    category_name=expense.get('category_name')
                ))
                total_expenses += expense_amount

            for income in incomes_data:
                income_id = income.get('id')
                income_amount = income.get('amount')
                income_date = income.get('date')
                if income_id is None or income_amount is None or income_date is None:
                    self.logger.warning(f"Skipping incomplete income record: {income}")
                    continue
                transactions.append(AccountTransaction(
                    id=income_id,
                    amount=income_amount,
                    description=income.get('description'),
                    date=income_date,
                    type='income',
                    category_id=income.get('category_id'),
                    category_name=income.get('category_name')
                ))
                total_income += income_amount
            
            # Sort transactions by date (most recent first)
            transactions.sort(key=lambda x: x.date, reverse=True)
            
            # Create account summary
            account_summary = AccountSummary(
                id=account.id,
                name=account.name,
                type=account.type,
                currency=account.currency,
                balance=account.balance,
                is_active=account.is_active,
                transaction_count=len(transactions),
                last_transaction_date=transactions[0].date if transactions else None
            )
            
            return AccountTransactionSummary(
                account=account_summary,
                transactions=transactions,
                total_income=total_income,
                total_expenses=total_expenses,
                net_change=total_income - total_expenses
            )
            
        except Exception as e:
            self.logger.error(f"Failed to fetch account transactions: {e}")
            raise AccountValidationError(f"Failed to fetch transactions: {str(e)}", AccountErrorCode.EXTERNAL_SERVICE_ERROR)

    def get_user_account_summaries(self, user_id: int, workspace_id: UUID) -> List[AccountSummary]:
        """Get summaries for all accounts in the workspace"""
        try:
            # 1. Authorize workspace access (viewer role required)
            self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_account_summaries")
            
            # 2. Filter by workspace
            accounts = self.db.query(Account).filter(
                Account.workspace_id == workspace_id,
                Account.is_archived == False
            ).all()
            
            def _fetch_account_summary(account):
                """Fetch transaction data for a single account."""
                try:
                    expense_response = self.expense_client.get_expenses_by_account(account.id, user_id)
                    income_response = self.income_client.get_incomes_by_account(account.id, user_id)

                    expense_count = len(expense_response) if not isinstance(expense_response, dict) else 0
                    income_count = len(income_response) if not isinstance(income_response, dict) else 0
                    total_transactions = expense_count + income_count

                    last_transaction_date = None
                    if expense_response and not isinstance(expense_response, dict):
                        expense_dates = [exp.get('date') for exp in expense_response if exp.get('date')]
                        if expense_dates:
                            last_transaction_date = max(expense_dates)

                    if income_response and not isinstance(income_response, dict):
                        income_dates = [inc.get('date') for inc in income_response if inc.get('date')]
                        if income_dates:
                            max_income_date = max(income_dates)
                            if not last_transaction_date or max_income_date > last_transaction_date:
                                last_transaction_date = max_income_date

                except Exception as e:
                    self.logger.warning(f"Failed to fetch transaction data for account {account.id}: {e}")
                    total_transactions = 0
                    last_transaction_date = None

                return AccountSummary(
                    id=account.id,
                    name=account.name,
                    type=account.type,
                    currency=account.currency,
                    balance=account.balance,
                    is_active=account.is_active,
                    transaction_count=total_transactions,
                    last_transaction_date=last_transaction_date
                )

            with ThreadPoolExecutor(max_workers=5) as executor:
                summaries = list(executor.map(_fetch_account_summary, accounts))
            
            return summaries
            
        except Exception as e:
            self.logger.error(f"Failed to get user account summaries: {e}")
            raise AccountValidationError(f"Failed to fetch account summaries: {str(e)}", AccountErrorCode.EXTERNAL_SERVICE_ERROR)

    def validate_account_ownership(self, account_id: int, user_id: int, workspace_id: UUID = None) -> bool:
        """Validate that an account exists and belongs to the user"""
        try:
            filters = [
                Account.id == account_id,
                Account.owner_id == user_id,
                Account.is_archived == False
            ]
            if workspace_id is not None:
                filters.append(Account.workspace_id == workspace_id)
            account = self.db.query(Account).filter(*filters).first()
            return account is not None
        except Exception as e:
            self.logger.error(f"Error validating account ownership: {e}")
            return False

    async def get_account_statistics(self, user_id: int, workspace_id: UUID) -> AccountStatisticsResponse:
        """Get statistics about accounts in the workspace with currency conversion"""
        try:
            # 1. Authorize workspace access (viewer role required)
            self.authorize_workspace_access(workspace_id, user_id, "viewer", "get_account_statistics")
            # Get user's base currency
            user_currency = self.user_client.get_user_base_currency(user_id)
            
            # Get all non-archived accounts in the workspace
            accounts = self.db.query(Account).filter(
                Account.workspace_id == workspace_id,
                Account.is_archived == False
            ).all()
            
            total_accounts = len(accounts)
            active_accounts = sum(1 for account in accounts if account.balance > 0)
            
            # Fetch rates once for batch conversion
            rates = None
            try:
                if hasattr(self.currency_client, 'get_rates'):
                    rates_result = self.currency_client.get_rates(user_currency)
                    # Handle both sync and async
                    if hasattr(rates_result, '__await__'):
                        rates = await rates_result
                    else:
                        rates = rates_result
            except Exception as e:
                self.logger.warning(f"Could not fetch rates for {user_currency}: {e}")

            # Calculate total balance with currency conversion
            total_balance = 0.0
            unconvertible_count = 0

            for account in accounts:
                account_balance = float(abs(account.balance))
                account_currency = account.currency or settings.DEFAULT_CURRENCY

                if account_currency != user_currency:
                    converted_amount = None
                    if rates:
                        converted_amount = CurrencyServiceClient.convert_with_rates(
                            account_balance, account_currency, user_currency, rates
                        )
                    if converted_amount is not None:
                        total_balance += converted_amount
                    else:
                        unconvertible_count += 1
                        self.logger.warning(f"Could not convert account {account.id} from {account_currency} to {user_currency}")
                else:
                    total_balance += account_balance
            
            return AccountStatisticsResponse(
                total_accounts=total_accounts,
                active_accounts=active_accounts,
                total_balance=round(total_balance, 2),
                currency=user_currency,
                unconvertible_accounts_count=unconvertible_count
            )
            
        except (AccountNotFoundError, AccountValidationError, AccountOwnershipError):
            raise
