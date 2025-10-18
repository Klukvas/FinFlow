from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime

from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate, AccountSummary, AccountTransaction, AccountTransactionSummary
from app.exceptions import (
    AccountNotFoundError,
    AccountValidationError,
    AccountOwnershipError,
    AccountArchivedError,
    AccountBalanceError
)
from app.utils.logger import get_logger, log_operation
from app.utils.validation import validate_currency_code, validate_balance, validate_account_name, validate_account_description, sanitize_input
from app.clients.expense_service_client import ExpenseServiceClient
from app.clients.income_service_client import IncomeServiceClient
from app.clients.currency_service_client import CurrencyServiceClient

class AccountService:
    def __init__(self, db: Session, expense_client: ExpenseServiceClient = None, income_client: IncomeServiceClient = None, currency_client: CurrencyServiceClient = None):
        self.db = db
        self.logger = get_logger(__name__)
        self.expense_client = expense_client or ExpenseServiceClient()
        self.income_client = income_client or IncomeServiceClient()
        self.currency_client = currency_client or CurrencyServiceClient()

    def create_account(self, account_data: AccountCreate, user_id: int) -> Account:
        """Create a new account for a user"""
        try:
            # Validate input
            if not validate_account_name(account_data.name):
                raise AccountValidationError("Invalid account name")
            
            if not validate_currency_code(account_data.currency):
                raise AccountValidationError("Invalid currency code")
            
            if not validate_balance(account_data.balance):
                raise AccountValidationError("Invalid balance amount")
            
            if not validate_account_description(account_data.description):
                raise AccountValidationError("Invalid description length")

            # Create account
            account = Account(
                name=sanitize_input(account_data.name),
                type=account_data.type,
                currency=account_data.currency.upper(),
                balance=account_data.balance,
                description=sanitize_input(account_data.description) if account_data.description else None,
                owner_id=user_id
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
            raise AccountValidationError("Account creation failed due to data constraints")
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Unexpected error creating account: {e}")
            raise AccountValidationError(f"Failed to create account: {str(e)}")

    def get_account(self, account_id: int, user_id: int) -> Account:
        """Get a specific account by ID, ensuring user ownership"""
        account = self.db.query(Account).filter(
            Account.id == account_id,
            Account.owner_id == user_id
        ).first()
        
        if not account:
            raise AccountNotFoundError(account_id)
        
        return account

    def get_user_accounts(self, user_id: int, include_archived: bool = False) -> List[Account]:
        """Get all accounts for a user"""
        query = self.db.query(Account).filter(Account.owner_id == user_id)
        
        if not include_archived:
            query = query.filter(Account.is_archived == False)
        
        return query.order_by(Account.created_at.desc()).all()

    def update_account(self, account_id: int, account_data: AccountUpdate, user_id: int) -> Account:
        """Update an existing account"""
        account = self.get_account(account_id, user_id)
        
        if account.is_archived:
            raise AccountArchivedError(account_id)
        
        # Validate updates
        if account_data.name is not None and not validate_account_name(account_data.name):
            raise AccountValidationError("Invalid account name")
        
        if account_data.currency is not None and not validate_currency_code(account_data.currency):
            raise AccountValidationError("Invalid currency code")
        
        if account_data.balance is not None and not validate_balance(account_data.balance):
            raise AccountValidationError("Invalid balance amount")
        
        if account_data.description is not None and not validate_account_description(account_data.description):
            raise AccountValidationError("Invalid description length")

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
            raise AccountValidationError(f"Failed to update account: {str(e)}")

    def archive_account(self, account_id: int, user_id: int) -> Account:
        """Archive an account (soft delete)"""
        account = self.get_account(account_id, user_id)
        
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
            raise AccountValidationError(f"Failed to archive account: {str(e)}")

    def update_balance(self, account_id: int, new_balance: float, user_id: int) -> Account:
        """Update account balance"""
        account = self.get_account(account_id, user_id)
        
        if account.is_archived:
            raise AccountArchivedError(account_id)
        
        if not validate_balance(new_balance):
            raise AccountBalanceError("Invalid balance amount")
        
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
            raise AccountBalanceError(f"Failed to update balance: {str(e)}")

    async def update_balance_with_conversion(
        self, 
        account_id: int, 
        amount_change: float, 
        transaction_currency: str, 
        user_id: int
    ) -> Account:
        """
        Update account balance with automatic currency conversion.
        
        Args:
            account_id: ID of the account to update
            amount_change: Amount to add (positive) or subtract (negative)
            transaction_currency: Currency of the transaction
            user_id: ID of the user (for ownership validation)
        
        Returns:
            Updated account
        """
        account = self.get_account(account_id, user_id)
        
        if account.is_archived:
            raise AccountArchivedError(account_id)
        
        if not validate_balance(abs(amount_change)):
            raise AccountBalanceError("Invalid amount")
        
        try:
            # If currencies are the same, no conversion needed
            if transaction_currency.upper() == account.currency.upper():
                new_balance = account.balance + amount_change
                if new_balance < 0:
                    raise AccountBalanceError("Insufficient funds in account")
                
                return self.update_balance(account_id, new_balance, user_id)
            
            # Convert amount to account currency (always use positive amount for conversion)
            converted_amount = await self.currency_client.convert_amount(
                abs(amount_change), 
                transaction_currency.upper(), 
                account.currency.upper()
            )
            
            if converted_amount is None:
                self.logger.error(f"Failed to convert {amount_change} {transaction_currency} to {account.currency}")
                raise AccountBalanceError(f"Currency conversion failed: {transaction_currency} to {account.currency}")
            
            # Restore the original sign after conversion
            final_amount = converted_amount if amount_change >= 0 else -converted_amount
            new_balance = account.balance + final_amount
            if new_balance < 0:
                raise AccountBalanceError("Insufficient funds in account")
            
            self.logger.info(
                f"Converted {amount_change} {transaction_currency} to {final_amount} {account.currency} "
                f"for account {account_id}"
            )
            
            return self.update_balance(account_id, new_balance, user_id)
            
        except AccountBalanceError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in balance update with conversion: {e}")
            raise AccountBalanceError(f"Failed to update balance with conversion: {str(e)}")

    def get_account_summary(self, account_id: int, user_id: int) -> AccountSummary:
        """Get account summary with transaction counts"""
        account = self.get_account(account_id, user_id)
        
        # Get transaction counts from external services
        try:
            expenses = self.expense_client.get_expenses_by_account(account_id, user_id, limit=1)
            incomes = self.income_client.get_incomes_by_account(account_id, user_id, limit=1)
            
            transaction_count = len(expenses) + len(incomes)
            last_transaction_date = None
            
            # Get the most recent transaction date
            all_transactions = []
            if expenses:
                all_transactions.extend([(exp.get('date'), 'expense') for exp in expenses])
            if incomes:
                all_transactions.extend([(inc.get('date'), 'income') for inc in incomes])
            
            if all_transactions:
                # Sort by date and get the most recent
                all_transactions.sort(key=lambda x: x[0], reverse=True)
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

    def get_account_transactions(self, account_id: int, user_id: int, limit: int = 100, offset: int = 0) -> AccountTransactionSummary:
        """Get account transactions from both expense and income services"""
        account = self.get_account(account_id, user_id)
        
        try:
            # Fetch transactions from both services
            expenses_data = self.expense_client.get_expenses_by_account(account_id, user_id, limit, offset)
            incomes_data = self.income_client.get_incomes_by_account(account_id, user_id, limit, offset)
            
            # Convert to transaction objects
            transactions = []
            total_income = 0.0
            total_expenses = 0.0
            
            for expense in expenses_data:
                transactions.append(AccountTransaction(
                    id=expense['id'],
                    amount=-expense['amount'],  # Expenses are negative
                    description=expense.get('description'),
                    date=expense['date'],
                    type='expense',
                    category_id=expense.get('category_id'),
                    category_name=expense.get('category_name')
                ))
                total_expenses += expense['amount']
            
            for income in incomes_data:
                transactions.append(AccountTransaction(
                    id=income['id'],
                    amount=income['amount'],
                    description=income.get('description'),
                    date=income['date'],
                    type='income',
                    category_id=income.get('category_id'),
                    category_name=income.get('category_name')
                ))
                total_income += income['amount']
            
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
            raise AccountValidationError(f"Failed to fetch transactions: {str(e)}")

    def get_user_account_summaries(self, user_id: int) -> List[AccountSummary]:
        """Get summaries for all user accounts"""
        try:
            accounts = self.db.query(Account).filter(
                Account.owner_id == user_id,
                Account.is_archived == False
            ).all()
            
            summaries = []
            for account in accounts:
                # Get transaction counts from expense and income services
                try:
                    expense_response = self.expense_client.get_expenses_by_account(account.id)
                    income_response = self.income_client.get_incomes_by_account(account.id)
                    
                    expense_count = len(expense_response) if not isinstance(expense_response, dict) else 0
                    income_count = len(income_response) if not isinstance(income_response, dict) else 0
                    total_transactions = expense_count + income_count
                    
                    # Get last transaction date
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
                
                summary = AccountSummary(
                    id=account.id,
                    name=account.name,
                    type=account.type,
                    currency=account.currency,
                    balance=account.balance,
                    is_active=account.is_active,
                    transaction_count=total_transactions,
                    last_transaction_date=last_transaction_date
                )
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            self.logger.error(f"Failed to get user account summaries: {e}")
            raise AccountValidationError(f"Failed to fetch account summaries: {str(e)}")

    def validate_account_ownership(self, account_id: int, user_id: int) -> bool:
        """Validate that an account exists and belongs to the user"""
        try:
            account = self.db.query(Account).filter(
                Account.id == account_id,
                Account.owner_id == user_id,
                Account.is_archived == False
            ).first()
            return account is not None
        except Exception as e:
            self.logger.error(f"Error validating account ownership: {e}")
            return False
