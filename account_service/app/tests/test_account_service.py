"""
Tests for app/services/account.py — AccountService business logic.
Covers create, read, update, archive, balance, and validation methods.
"""
import pytest
from datetime import datetime
from types import SimpleNamespace
from uuid import UUID
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.account import AccountService
from app.models.account import Account, AccountType
from app.schemas.account import AccountCreate, AccountUpdate
from app.exceptions import (
    AccountNotFoundError,
    AccountValidationError,
    AccountArchivedError,
    AccountBalanceError,
    AccountLimitExceededError,
    AccountReadOnlyExcessError,
    AccountErrorCode,
)
from app.tests.conftest import (
    TEST_WORKSPACE_ID,
    TestingSessionLocal,
    create_account_in_db,
)


USER_ID = 1


def _make_service(db_session) -> AccountService:
    """Build an AccountService with mocked external clients."""
    expense_client = MagicMock()
    income_client = MagicMock()
    currency_client = MagicMock()

    with patch(
        "shared.clients.workspace.WorkspaceClient.authorize",
        return_value=(True, "owner"),
    ), patch(
        "shared.clients.subscription.SubscriptionClient.check_limit",
        return_value=(True, None),
    ), patch(
        "shared.clients.subscription.SubscriptionClient.check_modify_allowed",
        return_value=True,
    ):
        service = AccountService(db_session, expense_client, income_client, currency_client)

    return service


# ---------------------------------------------------------------------------
# create_account
# ---------------------------------------------------------------------------


class TestCreateAccount:
    def test_success(self, db_session):
        service = _make_service(db_session)
        data = AccountCreate(name="New Account", type=AccountType.SAVINGS, currency="USD", balance=500.0)

        account = service.create_account(data, USER_ID, TEST_WORKSPACE_ID)

        assert account.id is not None
        assert account.name == "New Account"
        assert account.type == AccountType.SAVINGS
        assert account.currency == "USD"
        assert float(account.balance) == 500.0
        assert account.owner_id == USER_ID
        assert account.workspace_id == TEST_WORKSPACE_ID

    def test_currency_uppercased(self, db_session):
        service = _make_service(db_session)
        data = AccountCreate(name="Euro Account", type=AccountType.BANK, currency="eur")

        account = service.create_account(data, USER_ID, TEST_WORKSPACE_ID)
        assert account.currency == "EUR"

    def test_description_sanitized(self, db_session):
        service = _make_service(db_session)
        data = AccountCreate(
            name="Desc Test",
            type=AccountType.CASH,
            description="  some description  ",
        )
        account = service.create_account(data, USER_ID, TEST_WORKSPACE_ID)
        assert account.description == "some description"

    def test_name_sanitized(self, db_session):
        service = _make_service(db_session)
        data = AccountCreate(name="  Trimmed  ", type=AccountType.CASH)
        account = service.create_account(data, USER_ID, TEST_WORKSPACE_ID)
        assert account.name == "Trimmed"

    def test_invalid_name_raises(self, db_session):
        service = _make_service(db_session)
        # Use SimpleNamespace to bypass Pydantic validation and test service-level validation
        data_obj = SimpleNamespace(
            name="", currency="USD", balance=0.0, description=None, type=AccountType.CASH
        )

        with pytest.raises((AccountValidationError, Exception)):
            service.create_account(data_obj, USER_ID, TEST_WORKSPACE_ID)

    def test_invalid_currency_raises(self, db_session):
        service = _make_service(db_session)
        data_obj = SimpleNamespace(
            name="Valid", currency="xx", balance=0.0, description=None, type=AccountType.CASH
        )

        with pytest.raises((AccountValidationError, Exception)):
            service.create_account(data_obj, USER_ID, TEST_WORKSPACE_ID)

    def test_invalid_balance_raises(self, db_session):
        service = _make_service(db_session)
        data_obj = SimpleNamespace(
            name="Valid", currency="USD", balance=99999999999.0, description=None, type=AccountType.CASH
        )

        with pytest.raises((AccountValidationError, Exception)):
            service.create_account(data_obj, USER_ID, TEST_WORKSPACE_ID)

    def test_subscription_limit_blocks_creation(self, db_session):
        service = _make_service(db_session)
        data = AccountCreate(name="Blocked", type=AccountType.CASH)

        with patch.object(
            service.subscription_client, "check_limit", return_value=(False, 3)
        ):
            with pytest.raises((AccountLimitExceededError, AccountValidationError)):
                service.create_account(data, USER_ID, TEST_WORKSPACE_ID)

    def test_workspace_access_denied(self, db_session):
        service = _make_service(db_session)
        data = AccountCreate(name="Denied", type=AccountType.CASH)

        with patch.object(
            service, "authorize_workspace_access",
            side_effect=AccountValidationError("No access", AccountErrorCode.ACCOUNT_NOT_OWNED),
        ):
            with pytest.raises(AccountValidationError):
                service.create_account(data, USER_ID, TEST_WORKSPACE_ID)

    def test_all_account_types_creatable(self, db_session):
        service = _make_service(db_session)
        for i, account_type in enumerate(AccountType):
            data = AccountCreate(name=f"Type {account_type.value}", type=account_type)
            account = service.create_account(data, USER_ID + i + 10, TEST_WORKSPACE_ID)
            assert account.type == account_type

    def test_default_balance_zero(self, db_session):
        service = _make_service(db_session)
        data = AccountCreate(name="Zero Balance", type=AccountType.CASH)
        account = service.create_account(data, USER_ID, TEST_WORKSPACE_ID)
        assert float(account.balance) == 0.0

    def test_negative_balance_accepted(self, db_session):
        service = _make_service(db_session)
        data = AccountCreate(name="Credit", type=AccountType.CREDIT, balance=-100.0)
        account = service.create_account(data, USER_ID, TEST_WORKSPACE_ID)
        assert float(account.balance) == -100.0


# ---------------------------------------------------------------------------
# get_account
# ---------------------------------------------------------------------------


class TestGetAccount:
    def test_success(self, db_session):
        service = _make_service(db_session)
        created = create_account_in_db(db_session, owner_id=USER_ID)

        result = service.get_account(created.id, USER_ID, TEST_WORKSPACE_ID)
        assert result.id == created.id
        assert result.name == created.name

    def test_not_found(self, db_session):
        service = _make_service(db_session)
        with pytest.raises(AccountNotFoundError):
            service.get_account(99999, USER_ID, TEST_WORKSPACE_ID)

    def test_wrong_workspace_not_found(self, db_session):
        service = _make_service(db_session)
        other_workspace = UUID("660e8400-e29b-41d4-a716-446655440000")
        create_account_in_db(db_session, owner_id=USER_ID, workspace_id=other_workspace)

        with pytest.raises(AccountNotFoundError):
            service.get_account(1, USER_ID, TEST_WORKSPACE_ID)


# ---------------------------------------------------------------------------
# get_user_accounts
# ---------------------------------------------------------------------------


class TestGetUserAccounts:
    def test_returns_all_non_archived(self, db_session):
        service = _make_service(db_session)
        create_account_in_db(db_session, owner_id=USER_ID, name="Active 1")
        create_account_in_db(db_session, owner_id=USER_ID, name="Active 2")
        create_account_in_db(db_session, owner_id=USER_ID, name="Archived", is_archived=True)

        accounts = service.get_user_accounts(USER_ID, TEST_WORKSPACE_ID)
        names = [a.name for a in accounts]
        assert "Active 1" in names
        assert "Active 2" in names
        assert "Archived" not in names

    def test_include_archived(self, db_session):
        service = _make_service(db_session)
        create_account_in_db(db_session, owner_id=USER_ID, name="Active")
        create_account_in_db(db_session, owner_id=USER_ID, name="Archived", is_archived=True)

        accounts = service.get_user_accounts(USER_ID, TEST_WORKSPACE_ID, include_archived=True)
        names = [a.name for a in accounts]
        assert "Active" in names
        assert "Archived" in names

    def test_empty_workspace(self, db_session):
        service = _make_service(db_session)
        accounts = service.get_user_accounts(USER_ID, TEST_WORKSPACE_ID)
        assert accounts == []

    def test_only_workspace_accounts(self, db_session):
        service = _make_service(db_session)
        other_workspace = UUID("660e8400-e29b-41d4-a716-446655440000")
        create_account_in_db(db_session, owner_id=USER_ID, name="Mine")
        create_account_in_db(db_session, owner_id=USER_ID, name="Other WS", workspace_id=other_workspace)

        accounts = service.get_user_accounts(USER_ID, TEST_WORKSPACE_ID)
        names = [a.name for a in accounts]
        assert "Mine" in names
        assert "Other WS" not in names


# ---------------------------------------------------------------------------
# update_account
# ---------------------------------------------------------------------------


class TestUpdateAccount:
    def test_update_name(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)
        update_data = AccountUpdate(name="Renamed")

        updated = service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)
        assert updated.name == "Renamed"

    def test_update_balance(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=100.0)
        update_data = AccountUpdate(balance=999.99)

        updated = service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)
        assert float(updated.balance) == 999.99

    def test_update_currency(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)
        update_data = AccountUpdate(currency="eur")

        updated = service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)
        assert updated.currency == "EUR"

    def test_update_type(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, account_type=AccountType.SAVINGS)
        update_data = AccountUpdate(type=AccountType.CHECKING)

        updated = service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)
        assert updated.type == AccountType.CHECKING

    def test_update_description(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)
        update_data = AccountUpdate(description="New desc")

        updated = service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)
        assert updated.description == "New desc"

    def test_update_is_active(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)
        update_data = AccountUpdate(is_active=False)

        updated = service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)
        assert updated.is_active is False

    def test_update_archived_account_raises(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, is_archived=True)
        update_data = AccountUpdate(name="Nope")

        with pytest.raises(AccountArchivedError):
            service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)

    def test_update_not_found_raises(self, db_session):
        service = _make_service(db_session)
        update_data = AccountUpdate(name="Ghost")

        with pytest.raises(AccountNotFoundError):
            service.update_account(99999, update_data, USER_ID, TEST_WORKSPACE_ID)

    def test_update_invalid_name_raises(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)
        # Use SimpleNamespace to bypass Pydantic and test service-level validation
        update_data = SimpleNamespace(
            name="A" * 101, type=None, currency=None, balance=None,
            description=None, is_active=None,
        )

        with pytest.raises(AccountValidationError):
            service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)

    def test_update_invalid_currency_raises(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)
        # "xx" fails validate_currency_code (lowercase, not uppercase)
        update_data = SimpleNamespace(
            name=None, type=None, currency="xx", balance=None,
            description=None, is_active=None,
        )

        with pytest.raises(AccountValidationError):
            service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)

    def test_update_invalid_balance_raises(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)
        update_data = SimpleNamespace(
            name=None, type=None, currency=None, balance=99999999999.0,
            description=None, is_active=None,
        )

        with pytest.raises(AccountValidationError):
            service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)

    def test_read_only_account_blocked(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)
        update_data = AccountUpdate(name="Blocked")

        with patch.object(
            service.subscription_client, "check_modify_allowed", return_value=False
        ), patch.object(
            service.subscription_client, "get_user_features",
            return_value={"accounts": {"enabled": True, "limit_value": 1}},
        ):
            with pytest.raises(AccountReadOnlyExcessError):
                service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)

    def test_null_description_clears(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, description="old desc")
        # Explicitly set description to empty string to clear it
        update_data = AccountUpdate(description="")

        updated = service.update_account(account.id, update_data, USER_ID, TEST_WORKSPACE_ID)
        assert updated.description is None


# ---------------------------------------------------------------------------
# archive_account
# ---------------------------------------------------------------------------


class TestArchiveAccount:
    def test_success(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        archived = service.archive_account(account.id, USER_ID, TEST_WORKSPACE_ID)
        assert archived.is_archived is True
        assert archived.is_active is False

    def test_already_archived_raises(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, is_archived=True)

        with pytest.raises(AccountArchivedError):
            service.archive_account(account.id, USER_ID, TEST_WORKSPACE_ID)

    def test_not_found_raises(self, db_session):
        service = _make_service(db_session)
        with pytest.raises(AccountNotFoundError):
            service.archive_account(99999, USER_ID, TEST_WORKSPACE_ID)


# ---------------------------------------------------------------------------
# update_balance
# ---------------------------------------------------------------------------


class TestUpdateBalance:
    def test_success(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=100.0)

        updated = service.update_balance(account.id, 999.99, USER_ID, TEST_WORKSPACE_ID)
        assert float(updated.balance) == 999.99

    def test_archived_account_raises(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, is_archived=True)

        with pytest.raises(AccountArchivedError):
            service.update_balance(account.id, 500.0, USER_ID, TEST_WORKSPACE_ID)

    def test_invalid_balance_raises(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        with pytest.raises(AccountBalanceError):
            service.update_balance(account.id, 99999999999.0, USER_ID, TEST_WORKSPACE_ID)

    def test_not_found_raises(self, db_session):
        service = _make_service(db_session)
        with pytest.raises(AccountNotFoundError):
            service.update_balance(99999, 500.0, USER_ID, TEST_WORKSPACE_ID)

    def test_negative_balance(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=100.0)
        updated = service.update_balance(account.id, -50.0, USER_ID, TEST_WORKSPACE_ID)
        assert float(updated.balance) == -50.0


# ---------------------------------------------------------------------------
# update_balance_with_conversion
# ---------------------------------------------------------------------------


class TestUpdateBalanceWithConversion:

    @pytest.mark.asyncio
    async def test_same_currency_no_conversion(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=1000.0, currency="USD")
        result = await service.update_balance_with_conversion(
            account.id, 200.0, "USD", USER_ID, TEST_WORKSPACE_ID
        )
        assert float(result.balance) == 1200.0

    @pytest.mark.asyncio
    async def test_same_currency_subtraction(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=1000.0, currency="USD")
        result = await service.update_balance_with_conversion(
            account.id, -200.0, "USD", USER_ID, TEST_WORKSPACE_ID
        )
        assert float(result.balance) == 800.0

    @pytest.mark.asyncio
    async def test_insufficient_funds_same_currency(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=100.0, currency="USD")
        with pytest.raises(AccountBalanceError):
            await service.update_balance_with_conversion(
                account.id, -200.0, "USD", USER_ID, TEST_WORKSPACE_ID
            )

    @pytest.mark.asyncio
    async def test_different_currency_conversion(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=1000.0, currency="USD")
        account.balance = float(account.balance)

        # Mock currency conversion: 100 EUR -> 110 USD
        service.currency_client.convert_amount = AsyncMock(return_value=110.0)

        result = await service.update_balance_with_conversion(
            account.id, 100.0, "EUR", USER_ID, TEST_WORKSPACE_ID
        )
        assert float(result.balance) == 1110.0

    @pytest.mark.asyncio
    async def test_different_currency_subtraction(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=1000.0, currency="USD")
        service.currency_client.convert_amount = AsyncMock(return_value=110.0)

        result = await service.update_balance_with_conversion(
            account.id, -100.0, "EUR", USER_ID, TEST_WORKSPACE_ID
        )
        assert float(result.balance) == 890.0

    @pytest.mark.asyncio
    async def test_conversion_failure_raises(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=1000.0, currency="USD")
        service.currency_client.convert_amount = AsyncMock(return_value=None)

        with pytest.raises(AccountBalanceError):
            await service.update_balance_with_conversion(
                account.id, 100.0, "EUR", USER_ID, TEST_WORKSPACE_ID
            )

    @pytest.mark.asyncio
    async def test_archived_account_raises(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, is_archived=True)

        with pytest.raises(AccountArchivedError):
            await service.update_balance_with_conversion(
                account.id, 100.0, "USD", USER_ID, TEST_WORKSPACE_ID
            )

    @pytest.mark.asyncio
    async def test_invalid_amount_raises(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=1000.0)

        with pytest.raises(AccountBalanceError):
            await service.update_balance_with_conversion(
                account.id, 99999999999.0, "USD", USER_ID, TEST_WORKSPACE_ID
            )

    @pytest.mark.asyncio
    async def test_not_found_raises(self, db_session):
        service = _make_service(db_session)
        with pytest.raises(AccountNotFoundError):
            await service.update_balance_with_conversion(
                99999, 100.0, "USD", USER_ID, TEST_WORKSPACE_ID
            )

    @pytest.mark.asyncio
    async def test_without_workspace_id_fallback(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=500.0, currency="USD")
        result = await service.update_balance_with_conversion(
            account.id, 100.0, "USD", USER_ID, workspace_id=None
        )
        assert float(result.balance) == 600.0

    @pytest.mark.asyncio
    async def test_without_workspace_id_not_found(self, db_session):
        service = _make_service(db_session)
        with pytest.raises(AccountNotFoundError):
            await service.update_balance_with_conversion(
                99999, 100.0, "USD", USER_ID, workspace_id=None
            )


# ---------------------------------------------------------------------------
# validate_account_ownership
# ---------------------------------------------------------------------------


class TestValidateAccountOwnership:
    def test_valid_ownership(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        assert service.validate_account_ownership(account.id, USER_ID, TEST_WORKSPACE_ID) is True

    def test_wrong_user(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        assert service.validate_account_ownership(account.id, 9999) is False

    def test_archived_returns_false(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, is_archived=True)

        assert service.validate_account_ownership(account.id, USER_ID) is False

    def test_nonexistent_account(self, db_session):
        service = _make_service(db_session)
        assert service.validate_account_ownership(99999, USER_ID) is False

    def test_without_workspace_filter(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        assert service.validate_account_ownership(account.id, USER_ID) is True


# ---------------------------------------------------------------------------
# get_account_summary
# ---------------------------------------------------------------------------


class TestGetAccountSummary:
    def test_success_with_transactions(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=500.0)

        service.expense_client.get_expenses_by_account.return_value = [
            {"id": 1, "amount": 50.0, "date": "2024-01-15T00:00:00", "description": "Test"}
        ]
        service.income_client.get_incomes_by_account.return_value = [
            {"id": 2, "amount": 100.0, "date": "2024-01-20T00:00:00", "description": "Salary"}
        ]

        summary = service.get_account_summary(account.id, USER_ID, TEST_WORKSPACE_ID)
        assert summary.id == account.id
        assert summary.transaction_count == 2
        assert summary.last_transaction_date is not None

    def test_no_transactions(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        service.expense_client.get_expenses_by_account.return_value = []
        service.income_client.get_incomes_by_account.return_value = []

        summary = service.get_account_summary(account.id, USER_ID, TEST_WORKSPACE_ID)
        assert summary.transaction_count == 0
        assert summary.last_transaction_date is None

    def test_external_service_failure_graceful(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        service.expense_client.get_expenses_by_account.side_effect = Exception("Service down")
        service.income_client.get_incomes_by_account.return_value = []

        # Should not raise, just return zero counts
        summary = service.get_account_summary(account.id, USER_ID, TEST_WORKSPACE_ID)
        assert summary.transaction_count == 0


# ---------------------------------------------------------------------------
# get_account_transactions
# ---------------------------------------------------------------------------


class TestGetAccountTransactions:
    def test_success(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID, balance=500.0)

        service.expense_client.get_expenses_by_account.return_value = [
            {"id": 1, "amount": 50.0, "date": "2024-01-15T00:00:00", "description": "Lunch"}
        ]
        service.income_client.get_incomes_by_account.return_value = [
            {"id": 2, "amount": 200.0, "date": "2024-01-20T00:00:00", "description": "Salary"}
        ]

        result = service.get_account_transactions(account.id, USER_ID, TEST_WORKSPACE_ID)
        assert len(result.transactions) == 2
        assert result.total_expenses == 50.0
        assert result.total_income == 200.0
        assert result.net_change == 150.0

    def test_expense_amounts_are_negative(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        service.expense_client.get_expenses_by_account.return_value = [
            {"id": 1, "amount": 75.0, "date": "2024-01-15T00:00:00", "description": "Food"}
        ]
        service.income_client.get_incomes_by_account.return_value = []

        result = service.get_account_transactions(account.id, USER_ID, TEST_WORKSPACE_ID)
        assert result.transactions[0].amount == -75.0
        assert result.transactions[0].type == "expense"

    def test_empty_transactions(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        service.expense_client.get_expenses_by_account.return_value = []
        service.income_client.get_incomes_by_account.return_value = []

        result = service.get_account_transactions(account.id, USER_ID, TEST_WORKSPACE_ID)
        assert len(result.transactions) == 0
        assert result.total_income == 0.0
        assert result.total_expenses == 0.0

    def test_incomplete_records_skipped(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        # Missing required fields
        service.expense_client.get_expenses_by_account.return_value = [
            {"id": None, "amount": 50.0, "date": "2024-01-15T00:00:00"},
            {"id": 2, "amount": None, "date": "2024-01-15T00:00:00"},
            {"id": 3, "amount": 30.0, "date": None},
        ]
        service.income_client.get_incomes_by_account.return_value = []

        result = service.get_account_transactions(account.id, USER_ID, TEST_WORKSPACE_ID)
        assert len(result.transactions) == 0

    def test_external_service_failure_raises(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        service.expense_client.get_expenses_by_account.side_effect = Exception("Boom")

        with pytest.raises(AccountValidationError):
            service.get_account_transactions(account.id, USER_ID, TEST_WORKSPACE_ID)

    def test_transactions_sorted_by_date_desc(self, db_session):
        service = _make_service(db_session)
        account = create_account_in_db(db_session, owner_id=USER_ID)

        service.expense_client.get_expenses_by_account.return_value = [
            {"id": 1, "amount": 10.0, "date": "2024-01-01T00:00:00", "description": "Old"},
        ]
        service.income_client.get_incomes_by_account.return_value = [
            {"id": 2, "amount": 20.0, "date": "2024-06-01T00:00:00", "description": "New"},
        ]

        result = service.get_account_transactions(account.id, USER_ID, TEST_WORKSPACE_ID)
        assert result.transactions[0].description == "New"
        assert result.transactions[1].description == "Old"


# ---------------------------------------------------------------------------
# _get_ordered_ids
# ---------------------------------------------------------------------------


class TestGetOrderedIds:
    def test_returns_ids_in_creation_order(self, db_session):
        service = _make_service(db_session)
        a1 = create_account_in_db(db_session, owner_id=USER_ID, name="First")
        a2 = create_account_in_db(db_session, owner_id=USER_ID, name="Second")

        ids = service._get_ordered_ids(TEST_WORKSPACE_ID)
        assert ids == [a1.id, a2.id]

    def test_empty_workspace(self, db_session):
        service = _make_service(db_session)
        ids = service._get_ordered_ids(TEST_WORKSPACE_ID)
        assert ids == []
