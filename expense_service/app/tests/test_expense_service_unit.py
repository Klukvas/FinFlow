"""
Unit tests for ExpenseService - targeting the 60% coverage gap in app/services/expense.py.
Tests service methods directly with mocked dependencies.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from uuid import UUID
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.expense import ExpenseService
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.exceptions import (
    ExpenseNotFoundError,
    ExpenseValidationError,
    ExpenseAmountError,
    ExpenseDateError,
    ExpenseDescriptionError,
    ExternalServiceError,
    ExpenseLimitExceededError,
    ErrorCode,
)

WORKSPACE_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
USER_ID = 42


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """Return a MagicMock that looks like an SQLAlchemy Session."""
    return MagicMock()


@pytest.fixture
def category_client():
    return MagicMock()


@pytest.fixture
def account_client():
    return MagicMock()


@pytest.fixture
def service(db_session, category_client, account_client):
    """Return an ExpenseService with all external deps mocked."""
    with patch("app.services.workspace_authorization.WorkspaceClient.authorize", return_value=(True, "owner")):
        svc = ExpenseService(db_session, category_client, account_client)
    # Replace clients with fresh mocks after construction
    svc.category_client = category_client
    svc.account_client = account_client
    svc.currency_client = MagicMock()
    svc.user_client = MagicMock()
    svc.subscription_client = MagicMock()
    svc.subscription_client.check_expense_limit.return_value = True
    return svc


# ---------------------------------------------------------------------------
# _validate_amount tests
# ---------------------------------------------------------------------------

class TestValidateAmount:
    def test_valid_amount_returns_rounded_decimal(self, service):
        result = service._validate_amount(Decimal("25.555"))
        assert result == Decimal("25.56")

    def test_zero_amount_raises(self, service):
        with pytest.raises(ExpenseValidationError) as exc_info:
            service._validate_amount(Decimal("0"))
        assert exc_info.value.error_code == ErrorCode.EXPENSE_AMOUNT_INVALID

    def test_negative_amount_raises(self, service):
        with pytest.raises(ExpenseValidationError) as exc_info:
            service._validate_amount(Decimal("-1.00"))
        assert exc_info.value.error_code == ErrorCode.EXPENSE_AMOUNT_INVALID

    def test_max_amount_boundary_raises_at_exact_max(self, service):
        # The check is `amount > settings.MAX_AMOUNT`, so 999999.99 == MAX_AMOUNT raises
        with pytest.raises(ExpenseAmountError):
            service._validate_amount(Decimal("999999.99"))

    def test_amount_exceeding_max_raises(self, service):
        with pytest.raises(ExpenseAmountError):
            service._validate_amount(Decimal("1000000.00"))

    def test_rounding_down(self, service):
        result = service._validate_amount(Decimal("10.004"))
        assert result == Decimal("10.00")


# ---------------------------------------------------------------------------
# _validate_description tests
# ---------------------------------------------------------------------------

class TestValidateDescription:
    def test_none_description_returns_none(self, service):
        assert service._validate_description(None) is None

    def test_valid_description_stripped(self, service):
        assert service._validate_description("  hello  ") == "hello"

    def test_whitespace_only_returns_none(self, service):
        assert service._validate_description("   ") is None

    def test_description_at_max_length(self, service):
        desc = "x" * 500
        assert service._validate_description(desc) == desc

    def test_description_exceeding_max_raises(self, service):
        desc = "x" * 501
        with pytest.raises(ExpenseDescriptionError):
            service._validate_description(desc)


# ---------------------------------------------------------------------------
# _validate_date tests
# ---------------------------------------------------------------------------

class TestValidateDate:
    def test_none_returns_today(self, service):
        assert service._validate_date(None) == date.today()

    def test_today_passes(self, service):
        assert service._validate_date(date.today()) == date.today()

    def test_past_date_in_range_passes(self, service):
        past = date.today() - timedelta(days=30)
        assert service._validate_date(past) == past

    def test_future_date_raises(self, service):
        future = date.today() + timedelta(days=1)
        with pytest.raises(ExpenseDateError) as exc_info:
            service._validate_date(future)
        assert exc_info.value.error_code == ErrorCode.EXPENSE_DATE_FUTURE

    def test_too_old_date_raises(self, service):
        too_old = date.today().replace(year=date.today().year - 11)
        with pytest.raises(ExpenseDateError) as exc_info:
            service._validate_date(too_old)
        assert exc_info.value.error_code == ErrorCode.EXPENSE_DATE_TOO_OLD


# ---------------------------------------------------------------------------
# _validate_category tests
# ---------------------------------------------------------------------------

class TestValidateCategory:
    def test_success(self, service, category_client):
        category_client.validate_category.return_value = {"id": 1, "name": "Food"}
        result = service._validate_category(1, USER_ID, WORKSPACE_ID)
        assert result == {"id": 1, "name": "Food"}

    def test_client_raises_wraps_in_external_service_error(self, service, category_client):
        category_client.validate_category.side_effect = HTTPException(status_code=404, detail="not found")
        with pytest.raises(ExternalServiceError):
            service._validate_category(1, USER_ID, WORKSPACE_ID)


# ---------------------------------------------------------------------------
# _validate_account tests
# ---------------------------------------------------------------------------

class TestValidateAccount:
    def test_success(self, service, account_client):
        account_client.validate_account.return_value = {"account": {"id": 5, "currency": "USD"}}
        result = service._validate_account(5, USER_ID)
        assert result["account"]["id"] == 5

    def test_client_raises_wraps_in_external_service_error(self, service, account_client):
        account_client.validate_account.side_effect = Exception("connection refused")
        with pytest.raises(ExternalServiceError):
            service._validate_account(5, USER_ID)


# ---------------------------------------------------------------------------
# _handle_balance_updates tests
# ---------------------------------------------------------------------------

class TestHandleBalanceUpdates:
    def _make_expense(self, account_id, amount, currency="USD"):
        expense = MagicMock()
        expense.account_id = account_id
        expense.amount = amount
        expense.currency = currency
        return expense

    def test_no_change_does_nothing(self, service, account_client):
        expense = self._make_expense(1, 50.0)
        # Same account_id and same amount — no update expected
        service._handle_balance_updates(expense, 50.0, 1, USER_ID)
        account_client.update_account_balance.assert_not_called()

    def test_amount_changed_updates_balance(self, service, account_client):
        account_client.validate_account.return_value = {"account": {"currency": "USD"}}
        expense = self._make_expense(1, 100.0)
        # Old amount was 50, account stays same — should update
        service._handle_balance_updates(expense, 50.0, 1, USER_ID)
        account_client.update_account_balance.assert_called()

    def test_account_changed_restores_old_deducts_new(self, service, account_client):
        account_client.validate_account.return_value = {"account": {"currency": "USD"}}
        expense = self._make_expense(2, 100.0)
        # Account changed from 1 to 2
        service._handle_balance_updates(expense, 100.0, 1, USER_ID)
        assert account_client.update_account_balance.call_count == 2

    def test_currency_conversion_on_account_change(self, service, account_client):
        account_client.validate_account.return_value = {"account": {"currency": "EUR"}}
        service.currency_client.convert_amount.return_value = 90.0
        expense = self._make_expense(2, 100.0, currency="USD")
        service._handle_balance_updates(expense, 100.0, 1, USER_ID)
        service.currency_client.convert_amount.assert_called()

    def test_balance_update_exception_raises_validation_error(self, service, account_client):
        account_client.validate_account.side_effect = Exception("db error")
        expense = self._make_expense(2, 100.0)
        with pytest.raises(ExpenseValidationError) as exc_info:
            service._handle_balance_updates(expense, 100.0, 1, USER_ID)
        assert exc_info.value.error_code == ErrorCode.ACCOUNT_BALANCE_UPDATE_FAILED

    def test_old_account_none_no_restore(self, service, account_client):
        """When old_account_id is None, should only deduct from new account."""
        account_client.validate_account.return_value = {"account": {"currency": "USD"}}
        expense = self._make_expense(1, 100.0)
        service._handle_balance_updates(expense, 100.0, None, USER_ID)
        # Should call update_account_balance once (new account deduct)
        assert account_client.update_account_balance.call_count == 1


# ---------------------------------------------------------------------------
# get_all tests
# ---------------------------------------------------------------------------

class TestGetAll:
    def test_returns_workspace_expenses(self, service, db_session):
        mock_expense = MagicMock()
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_expense]
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            result = service.get_all(USER_ID, WORKSPACE_ID)
        assert result == [mock_expense]

    def test_exception_raises_validation_error(self, service, db_session):
        with patch.object(service, "authorize_workspace_access", side_effect=ExpenseValidationError("no access", ErrorCode.VALIDATION_ERROR)):
            with pytest.raises(ExpenseValidationError):
                service.get_all(USER_ID, WORKSPACE_ID)


# ---------------------------------------------------------------------------
# get_all_paginated tests
# ---------------------------------------------------------------------------

class TestGetAllPaginated:
    def test_returns_expenses_and_total(self, service, db_session):
        mock_expense = MagicMock()
        (db_session.query.return_value
            .filter.return_value
            .count.return_value) = 1
        (db_session.query.return_value
            .filter.return_value
            .order_by.return_value
            .offset.return_value
            .limit.return_value
            .all.return_value) = [mock_expense]

        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            expenses, total = service.get_all_paginated(USER_ID, WORKSPACE_ID, page=1, size=10)
        assert total == 1
        assert expenses == [mock_expense]

    def test_page_2_uses_correct_offset(self, service, db_session):
        (db_session.query.return_value
            .filter.return_value
            .count.return_value) = 25
        (db_session.query.return_value
            .filter.return_value
            .order_by.return_value
            .offset.return_value
            .limit.return_value
            .all.return_value) = []

        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            _, total = service.get_all_paginated(USER_ID, WORKSPACE_ID, page=2, size=10)
        assert total == 25

    def test_exception_wrapped_as_validation_error(self, service):
        with patch.object(service, "authorize_workspace_access", side_effect=ExpenseValidationError("no access", ErrorCode.VALIDATION_ERROR)):
            with pytest.raises(ExpenseValidationError):
                service.get_all_paginated(USER_ID, WORKSPACE_ID)


# ---------------------------------------------------------------------------
# get tests
# ---------------------------------------------------------------------------

class TestGet:
    def test_not_found_raises(self, service, db_session):
        db_session.query.return_value.filter.return_value.first.return_value = None
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with pytest.raises(ExpenseNotFoundError):
                service.get(9999, USER_ID, WORKSPACE_ID)

    def test_found_returns_expense(self, service, db_session):
        mock_expense = MagicMock()
        db_session.query.return_value.filter.return_value.first.return_value = mock_expense
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            result = service.get(1, USER_ID, WORKSPACE_ID)
        assert result == mock_expense


# ---------------------------------------------------------------------------
# update tests
# ---------------------------------------------------------------------------

class TestUpdate:
    def _make_expense(self):
        e = MagicMock()
        e.id = 1
        e.amount = 50.0
        e.account_id = None
        e.currency = "USD"
        e.category_id = None
        e.description = "old"
        e.date = date.today() - timedelta(days=1)
        return e

    def test_update_amount(self, service, db_session, account_client):
        expense = self._make_expense()
        db_session.query.return_value.filter.return_value.first.return_value = expense
        account_client.validate_account.return_value = {"account": {"currency": "USD"}}
        data = ExpenseUpdate(amount=75.0)
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with patch.object(service, "_handle_balance_updates"):
                service.update(1, data, USER_ID, WORKSPACE_ID)
        assert float(expense.amount) == 75.0

    def test_update_description(self, service, db_session):
        expense = self._make_expense()
        db_session.query.return_value.filter.return_value.first.return_value = expense
        data = ExpenseUpdate(description="new description")
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with patch.object(service, "_handle_balance_updates"):
                service.update(1, data, USER_ID, WORKSPACE_ID)
        assert expense.description == "new description"

    def test_update_date(self, service, db_session):
        expense = self._make_expense()
        db_session.query.return_value.filter.return_value.first.return_value = expense
        new_date = date.today() - timedelta(days=5)
        data = ExpenseUpdate(date=new_date)
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with patch.object(service, "_handle_balance_updates"):
                service.update(1, data, USER_ID, WORKSPACE_ID)
        assert expense.date == new_date

    def test_update_category_to_zero_sets_none(self, service, db_session):
        expense = self._make_expense()
        expense.category_id = 5
        db_session.query.return_value.filter.return_value.first.return_value = expense
        data = ExpenseUpdate(category_id=0)
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with patch.object(service, "_handle_balance_updates"):
                service.update(1, data, USER_ID, WORKSPACE_ID)
        assert expense.category_id is None

    def test_update_with_new_category_validates(self, service, db_session, category_client):
        expense = self._make_expense()
        db_session.query.return_value.filter.return_value.first.return_value = expense
        category_client.validate_category.return_value = {"id": 3}
        data = ExpenseUpdate(category_id=3)
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with patch.object(service, "_handle_balance_updates"):
                service.update(1, data, USER_ID, WORKSPACE_ID)
        category_client.validate_category.assert_called_once()
        assert expense.category_id == 3

    def test_update_currency(self, service, db_session):
        expense = self._make_expense()
        db_session.query.return_value.filter.return_value.first.return_value = expense
        data = ExpenseUpdate(currency="EUR")
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with patch.object(service, "_handle_balance_updates"):
                service.update(1, data, USER_ID, WORKSPACE_ID)
        assert expense.currency == "EUR"

    def test_update_not_found_raises(self, service, db_session):
        db_session.query.return_value.filter.return_value.first.return_value = None
        data = ExpenseUpdate(amount=10.0)
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with pytest.raises(ExpenseNotFoundError):
                service.update(9999, data, USER_ID, WORKSPACE_ID)

    def test_update_account(self, service, db_session, account_client):
        expense = self._make_expense()
        expense.account_id = 1
        db_session.query.return_value.filter.return_value.first.return_value = expense
        account_client.validate_account.return_value = {"account": {"currency": "USD"}}
        data = ExpenseUpdate(account_id=2)
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with patch.object(service, "_handle_balance_updates"):
                service.update(1, data, USER_ID, WORKSPACE_ID)
        assert expense.account_id == 2


# ---------------------------------------------------------------------------
# delete tests
# ---------------------------------------------------------------------------

class TestDelete:
    def _make_expense(self):
        e = MagicMock()
        e.id = 1
        e.amount = 50.0
        e.account_id = None
        e.currency = "USD"
        e.category_id = 1
        e.date = date.today()
        return e

    def test_delete_success(self, service, db_session):
        expense = self._make_expense()
        db_session.query.return_value.filter.return_value.first.return_value = expense
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            result = service.delete(1, USER_ID, WORKSPACE_ID)
        assert result == {"detail": "Expense deleted successfully"}
        db_session.delete.assert_called_once_with(expense)
        db_session.commit.assert_called()

    def test_delete_with_account_restores_balance(self, service, db_session, account_client):
        expense = self._make_expense()
        expense.account_id = 5
        db_session.query.return_value.filter.return_value.first.return_value = expense
        account_client.update_account_balance.return_value = {}
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            service.delete(1, USER_ID, WORKSPACE_ID)
        account_client.update_account_balance.assert_called_once_with(5, USER_ID, expense.amount, expense.currency)

    def test_delete_not_found_raises(self, service, db_session):
        db_session.query.return_value.filter.return_value.first.return_value = None
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with pytest.raises(ExpenseNotFoundError):
                service.delete(9999, USER_ID, WORKSPACE_ID)

    def test_delete_exception_wrapped(self, service, db_session):
        expense = self._make_expense()
        db_session.query.return_value.filter.return_value.first.return_value = expense
        db_session.commit.side_effect = Exception("db crash")
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with pytest.raises(ExpenseValidationError):
                service.delete(1, USER_ID, WORKSPACE_ID)


# ---------------------------------------------------------------------------
# create tests (service layer)
# ---------------------------------------------------------------------------

class TestCreate:
    def _make_data(self, **kwargs):
        defaults = {"amount": 50.0, "category_id": None, "account_id": None, "currency": "USD", "description": None, "date": None}
        defaults.update(kwargs)
        return ExpenseCreate(**defaults)

    def test_create_subscription_limit_exceeded_raises(self, service, db_session):
        service.subscription_client.check_expense_limit.return_value = False
        service.subscription_client.get_user_features.return_value = {
            "expenses": {"enabled": True, "limit_value": 10}
        }
        db_session.query.return_value.filter.return_value.count.return_value = 10
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with pytest.raises(ExpenseLimitExceededError):
                service.create(self._make_data(), USER_ID, WORKSPACE_ID)

    def test_create_with_account_deducts_balance(self, service, db_session, account_client):
        service.subscription_client.check_expense_limit.return_value = True
        db_session.query.return_value.filter.return_value.count.return_value = 0
        account_client.validate_account.return_value = {"account": {"currency": "USD"}}
        account_client.update_account_balance.return_value = {}

        created = MagicMock()
        created.id = 99
        db_session.refresh = MagicMock()

        data = self._make_data(amount=100.0, account_id=5)
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with patch.object(service.db, "add"), patch.object(service.db, "commit"), patch.object(service.db, "refresh"):
                service.create(data, USER_ID, WORKSPACE_ID)
        account_client.update_account_balance.assert_called_once()
        args = account_client.update_account_balance.call_args[0]
        # First positional arg is account_id
        assert args[0] == 5
        # Third is amount change (negative)
        assert args[2] < 0

    def test_create_with_currency_conversion(self, service, db_session, account_client):
        service.subscription_client.check_expense_limit.return_value = True
        db_session.query.return_value.filter.return_value.count.return_value = 0
        account_client.validate_account.return_value = {"account": {"currency": "EUR"}}
        account_client.update_account_balance.return_value = {}
        service.currency_client.convert_amount.return_value = 90.0

        data = self._make_data(amount=100.0, account_id=5, currency="USD")
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with patch.object(service.db, "add"), patch.object(service.db, "commit"), patch.object(service.db, "refresh"):
                service.create(data, USER_ID, WORKSPACE_ID)
        service.currency_client.convert_amount.assert_called_once_with(100.0, "USD", "EUR")

    def test_create_currency_conversion_none_uses_original(self, service, db_session, account_client):
        """When conversion returns None, use original amount."""
        service.subscription_client.check_expense_limit.return_value = True
        db_session.query.return_value.filter.return_value.count.return_value = 0
        account_client.validate_account.return_value = {"account": {"currency": "EUR"}}
        account_client.update_account_balance.return_value = {}
        service.currency_client.convert_amount.return_value = None  # Conversion failure

        data = self._make_data(amount=100.0, account_id=5, currency="USD")
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with patch.object(service.db, "add"), patch.object(service.db, "commit"), patch.object(service.db, "refresh"):
                service.create(data, USER_ID, WORKSPACE_ID)
        # Should still call update with original amount
        account_client.update_account_balance.assert_called_once()

    def test_create_db_error_rollback(self, service, db_session):
        service.subscription_client.check_expense_limit.return_value = True
        db_session.query.return_value.filter.return_value.count.return_value = 0
        db_session.add = MagicMock()
        db_session.commit.side_effect = Exception("db error")

        data = self._make_data(amount=50.0)
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with pytest.raises(ExpenseValidationError):
                service.create(data, USER_ID, WORKSPACE_ID)
        db_session.rollback.assert_called()


# ---------------------------------------------------------------------------
# Helper to build a real Expense ORM-like object for Pydantic validation
# ---------------------------------------------------------------------------

def _make_real_expense(
    expense_id=1,
    amount=100.0,
    currency="USD",
    user_id=USER_ID,
    workspace_id=WORKSPACE_ID,
    category_id=1,
    account_id=None,
    description=None,
    expense_date=None,
):
    from app.models.expense import Expense
    from datetime import date as _date
    e = Expense(
        id=expense_id,
        amount=amount,
        currency=currency,
        user_id=user_id,
        workspace_id=workspace_id,
        category_id=category_id,
        account_id=account_id,
        description=description,
        date=expense_date or _date.today(),
    )
    # Manually set the PK since we are not using a real DB session
    e.id = expense_id
    return e


# ---------------------------------------------------------------------------
# get_by_category tests
# ---------------------------------------------------------------------------

class TestGetByCategory:
    def test_returns_expenses_and_stats(self, service, db_session, category_client):
        expense = _make_real_expense(amount=100.0, currency="USD")
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [expense]
        category_client.validate_category.return_value = {"id": 1}
        service.user_client.get_user_base_currency.return_value = "USD"

        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            result = service.get_by_category(1, USER_ID, WORKSPACE_ID)
        assert result.statistics.count == 1
        assert result.statistics.total_amount == 100.0

    def test_user_currency_fetch_fails_defaults_usd(self, service, db_session, category_client):
        expense = _make_real_expense(amount=50.0, currency="USD")
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [expense]
        category_client.validate_category.return_value = {"id": 1}
        service.user_client.get_user_base_currency.side_effect = Exception("service down")

        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            result = service.get_by_category(1, USER_ID, WORKSPACE_ID)
        assert result.statistics.currency == "USD"

    def test_currency_conversion_applied(self, service, db_session, category_client):
        expense = _make_real_expense(amount=100.0, currency="USD")
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [expense]
        category_client.validate_category.return_value = {"id": 1}
        service.user_client.get_user_base_currency.return_value = "EUR"
        service.currency_client.convert_amount.return_value = 90.0

        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            result = service.get_by_category(1, USER_ID, WORKSPACE_ID)
        assert result.statistics.total_amount == 90.0

    def test_currency_conversion_returns_none_uses_original(self, service, db_session, category_client):
        expense = _make_real_expense(amount=100.0, currency="USD")
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [expense]
        category_client.validate_category.return_value = {"id": 1}
        service.user_client.get_user_base_currency.return_value = "EUR"
        service.currency_client.convert_amount.return_value = None  # Conversion fails

        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            result = service.get_by_category(1, USER_ID, WORKSPACE_ID)
        # Should fall back to original amount
        assert result.statistics.total_amount == 100.0

    def test_empty_category_returns_zero_stats(self, service, db_session, category_client):
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        category_client.validate_category.return_value = {"id": 1}
        service.user_client.get_user_base_currency.return_value = "USD"

        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            result = service.get_by_category(1, USER_ID, WORKSPACE_ID)
        assert result.statistics.count == 0
        assert result.statistics.total_amount == 0.0
        assert result.statistics.average_amount == 0.0

    def test_multiple_expenses_averages_correctly(self, service, db_session, category_client):
        expenses = [
            _make_real_expense(expense_id=1, amount=100.0, currency="USD"),
            _make_real_expense(expense_id=2, amount=200.0, currency="USD"),
        ]
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = expenses
        category_client.validate_category.return_value = {"id": 1}
        service.user_client.get_user_base_currency.return_value = "USD"

        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            result = service.get_by_category(1, USER_ID, WORKSPACE_ID)
        assert result.statistics.count == 2
        assert result.statistics.total_amount == 300.0
        assert result.statistics.average_amount == 150.0


# ---------------------------------------------------------------------------
# get_by_date_range tests
# ---------------------------------------------------------------------------

class TestGetByDateRange:
    def test_valid_range_returns_expenses(self, service, db_session):
        mock_expense = MagicMock()
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_expense]
        start = date.today() - timedelta(days=10)
        end = date.today()
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            result = service.get_by_date_range(start, end, USER_ID, WORKSPACE_ID)
        assert result == [mock_expense]

    def test_start_after_end_raises(self, service):
        start = date.today()
        end = date.today() - timedelta(days=1)
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            with pytest.raises(ExpenseValidationError) as exc_info:
                service.get_by_date_range(start, end, USER_ID, WORKSPACE_ID)
        # The inner INVALID_DATE_RANGE error is re-raised wrapped in EXPENSE_RETRIEVAL_FAILED
        assert exc_info.value.error_code == ErrorCode.EXPENSE_RETRIEVAL_FAILED

    def test_same_start_and_end_passes(self, service, db_session):
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        today = date.today()
        with patch.object(service, "authorize_workspace_access", return_value="owner"):
            result = service.get_by_date_range(today, today, USER_ID, WORKSPACE_ID)
        assert result == []
