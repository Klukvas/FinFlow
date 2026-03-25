"""
Tests for app/services/income.py — IncomeService CRUD operations,
filtering, pagination, validation, and statistics.
"""
import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.income import IncomeService
from app.schemas.income import IncomeCreate, IncomeUpdate, IncomeOut
from app.models.income import Income
from app.clients.account_service_client import AccountServiceClient
from app.exceptions import (
    IncomeNotFoundError,
    IncomeValidationError,
    IncomeAmountError,
    IncomeDateError,
    IncomeDescriptionError,
    ExternalServiceError,
    IncomeLimitExceededError,
    IncomeErrorCodes,
)
from app.tests.conftest import TEST_USER_ID, TEST_WORKSPACE_ID


@pytest.fixture
def mock_account_client():
    client = MagicMock(spec=AccountServiceClient)
    client.validate_account = AsyncMock(return_value={"account": {"id": 1}})
    client.update_account_balance = AsyncMock(return_value={"account": {"id": 1, "balance": 100.0}})
    return client


@pytest.fixture
def income_service(db_session, mock_account_client):
    """Create an IncomeService with mocked external clients."""
    with patch("app.services.income.CategoryServiceClient") as mock_cat, \
         patch("app.services.income.CurrencyServiceClient") as mock_curr, \
         patch("shared.clients.subscription.SubscriptionClient.get_instance") as mock_sub:

        mock_cat_instance = MagicMock()
        mock_cat_instance.validate_category = AsyncMock(return_value={"category": {"id": 1}})
        mock_cat.return_value = mock_cat_instance

        mock_curr_instance = MagicMock()
        mock_curr_instance.get_user_base_currency = MagicMock(return_value="USD")
        mock_curr_instance.get_rates = AsyncMock(return_value={"USD": 1.0, "EUR": 0.85})
        mock_curr_instance.convert_with_rates = CurrencyServiceClientConvertStub
        mock_curr.return_value = mock_curr_instance

        mock_sub_instance = MagicMock()
        mock_sub_instance.check_limit = MagicMock(return_value=(True, None))
        mock_sub_instance.get_user_features = MagicMock(return_value={})
        mock_sub.return_value = mock_sub_instance

        service = IncomeService(db_session, mock_account_client)
        # Override the internally created clients with our mocks
        service.category_client = mock_cat_instance
        service.currency_client = mock_curr_instance
        service.subscription_client = mock_sub_instance

        yield service


def CurrencyServiceClientConvertStub(amount, from_currency, to_currency, rates):
    """Stub for convert_with_rates static method."""
    if from_currency == to_currency:
        return amount
    from_rate = rates.get(from_currency)
    to_rate = rates.get(to_currency)
    if from_rate and to_rate:
        return round(amount * (to_rate / from_rate), 2)
    return None


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
class TestIncomeServiceCreate:
    @pytest.mark.asyncio
    async def test_create_minimal_income(self, income_service):
        payload = IncomeCreate(amount=500.0, currency="USD", date="2025-01-15")
        result = await income_service.create(payload, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.amount == 500.0
        assert result.user_id == TEST_USER_ID
        assert result.workspace_id == TEST_WORKSPACE_ID
        assert result.currency == "USD"

    @pytest.mark.asyncio
    async def test_create_with_category(self, income_service):
        payload = IncomeCreate(amount=300.0, category_id=5, date="2025-01-15")
        result = await income_service.create(payload, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.category_id == 5
        income_service.category_client.validate_category.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_account_updates_balance(self, income_service, mock_account_client):
        payload = IncomeCreate(amount=1000.0, account_id=10, currency="USD", date="2025-01-15")
        result = await income_service.create(payload, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.account_id == 10
        mock_account_client.validate_account.assert_called_once()
        mock_account_client.update_account_balance.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_description(self, income_service):
        payload = IncomeCreate(amount=200.0, description="Freelance project", date="2025-02-01")
        result = await income_service.create(payload, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.description == "Freelance project"

    @pytest.mark.asyncio
    async def test_create_without_date_defaults_to_now(self, income_service):
        payload = IncomeCreate(amount=100.0)
        result = await income_service.create(payload, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.date is not None
        assert result.date.date() == datetime.utcnow().date()

    @pytest.mark.asyncio
    async def test_create_negative_amount_raises(self, income_service):
        """Amount validation in the service (even though Pydantic should catch it first)."""
        payload = IncomeCreate(amount=0.01)
        # Force amount to be invalid via direct attribute override
        payload_dict = payload.model_dump()
        payload_dict["amount"] = -5.0
        bad_payload = MagicMock()
        bad_payload.amount = -5.0
        bad_payload.category_id = None
        bad_payload.account_id = None
        bad_payload.currency = "USD"
        bad_payload.description = None
        bad_payload.date = None

        with pytest.raises(IncomeAmountError):
            await income_service.create(bad_payload, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_create_amount_too_large_raises(self, income_service):
        bad_payload = MagicMock()
        bad_payload.amount = 1_000_000.00
        bad_payload.category_id = None
        bad_payload.account_id = None
        bad_payload.currency = "USD"
        bad_payload.description = None
        bad_payload.date = None

        with pytest.raises(IncomeAmountError):
            await income_service.create(bad_payload, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_create_invalid_date_format_raises(self, income_service):
        payload = IncomeCreate(amount=100.0, date="not-a-date")

        with pytest.raises(IncomeDateError):
            await income_service.create(payload, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_create_future_date_raises(self, income_service):
        future = (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%d")
        payload = IncomeCreate(amount=100.0, date=future)

        with pytest.raises(IncomeDateError):
            await income_service.create(payload, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_create_long_description_raises(self, income_service):
        bad_payload = MagicMock()
        bad_payload.amount = 100.0
        bad_payload.category_id = None
        bad_payload.account_id = None
        bad_payload.currency = "USD"
        bad_payload.description = "x" * 501
        bad_payload.date = None

        with pytest.raises(IncomeDescriptionError):
            await income_service.create(bad_payload, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_create_limit_exceeded_raises(self, income_service):
        income_service.subscription_client.check_limit.return_value = (False, 10)
        payload = IncomeCreate(amount=100.0, date="2025-01-15")

        with pytest.raises(IncomeLimitExceededError):
            await income_service.create(payload, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_create_compensates_balance_on_failure(self, income_service, mock_account_client):
        """If DB commit fails after balance update, the balance should be compensated."""
        payload = IncomeCreate(amount=500.0, account_id=10, currency="USD", date="2025-01-15")

        with patch.object(income_service.db, "commit", side_effect=Exception("DB error")):
            with pytest.raises(IncomeValidationError):
                await income_service.create(payload, TEST_USER_ID, TEST_WORKSPACE_ID)

        # Balance was updated, so compensation should be attempted
        assert mock_account_client.update_account_balance.call_count >= 2

    @pytest.mark.asyncio
    async def test_create_rounds_amount(self, income_service):
        payload = IncomeCreate(amount=99.999, date="2025-01-15")
        result = await income_service.create(payload, TEST_USER_ID, TEST_WORKSPACE_ID)
        assert result.amount == 100.0


# ---------------------------------------------------------------------------
# GET BY ID
# ---------------------------------------------------------------------------
class TestIncomeServiceGetById:
    def test_get_existing_income(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=250.0, description="Test get")
        result = income_service.get_by_id(income.id, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.id == income.id
        assert result.amount == 250.0

    def test_get_nonexistent_income_raises(self, income_service):
        with pytest.raises(IncomeNotFoundError):
            income_service.get_by_id(99999, TEST_USER_ID, TEST_WORKSPACE_ID)

    def test_get_income_wrong_workspace(self, income_service, create_income_in_db):
        other_ws = uuid4()
        income = create_income_in_db(workspace_id=other_ws)

        with pytest.raises(IncomeNotFoundError):
            income_service.get_by_id(income.id, TEST_USER_ID, TEST_WORKSPACE_ID)


# ---------------------------------------------------------------------------
# GET ALL
# ---------------------------------------------------------------------------
class TestIncomeServiceGetAll:
    def test_get_all_empty(self, income_service):
        result = income_service.get_all(TEST_USER_ID, TEST_WORKSPACE_ID)
        assert result == []

    def test_get_all_returns_incomes(self, income_service, create_income_in_db):
        create_income_in_db(amount=100.0)
        create_income_in_db(amount=200.0)
        result = income_service.get_all(TEST_USER_ID, TEST_WORKSPACE_ID)
        assert len(result) == 2

    def test_get_all_with_skip_and_limit(self, income_service, create_income_in_db):
        for i in range(5):
            create_income_in_db(amount=float(i * 100))
        result = income_service.get_all(TEST_USER_ID, TEST_WORKSPACE_ID, skip=2, limit=2)
        assert len(result) == 2

    def test_get_all_filters_by_workspace(self, income_service, create_income_in_db):
        create_income_in_db(amount=100.0)
        create_income_in_db(amount=200.0, workspace_id=uuid4())  # different workspace
        result = income_service.get_all(TEST_USER_ID, TEST_WORKSPACE_ID)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# GET BY DATE RANGE
# ---------------------------------------------------------------------------
class TestIncomeServiceGetByDateRange:
    def test_date_range_returns_filtered(self, income_service, create_income_in_db):
        create_income_in_db(amount=100.0, income_date=datetime(2025, 1, 15))
        create_income_in_db(amount=200.0, income_date=datetime(2025, 2, 15))
        create_income_in_db(amount=300.0, income_date=datetime(2025, 3, 15))

        result = income_service.get_by_date_range(
            TEST_USER_ID, TEST_WORKSPACE_ID,
            date(2025, 1, 1), date(2025, 2, 28)
        )
        assert len(result) == 2

    def test_date_range_start_after_end_raises(self, income_service):
        with pytest.raises(IncomeValidationError):
            income_service.get_by_date_range(
                TEST_USER_ID, TEST_WORKSPACE_ID,
                date(2025, 3, 1), date(2025, 1, 1)
            )


# ---------------------------------------------------------------------------
# GET ALL PAGINATED
# ---------------------------------------------------------------------------
class TestIncomeServiceGetAllPaginated:
    def test_paginated_returns_tuple(self, income_service, create_income_in_db):
        for _ in range(3):
            create_income_in_db(amount=100.0)

        incomes, total = income_service.get_all_paginated(TEST_USER_ID, TEST_WORKSPACE_ID, page=1, size=2)
        assert len(incomes) == 2
        assert total == 3

    def test_paginated_page_2(self, income_service, create_income_in_db):
        for _ in range(5):
            create_income_in_db(amount=100.0)

        incomes, total = income_service.get_all_paginated(TEST_USER_ID, TEST_WORKSPACE_ID, page=2, size=3)
        assert len(incomes) == 2
        assert total == 5

    def test_paginated_empty(self, income_service):
        incomes, total = income_service.get_all_paginated(TEST_USER_ID, TEST_WORKSPACE_ID)
        assert incomes == []
        assert total == 0


# ---------------------------------------------------------------------------
# GET BY CATEGORY
# ---------------------------------------------------------------------------
class TestIncomeServiceGetByCategory:
    @pytest.mark.asyncio
    async def test_get_by_category_returns_incomes_and_stats(self, income_service, create_income_in_db):
        create_income_in_db(amount=100.0, category_id=5)
        create_income_in_db(amount=200.0, category_id=5)
        create_income_in_db(amount=300.0, category_id=99)  # different category

        result = await income_service.get_by_category(5, TEST_USER_ID, TEST_WORKSPACE_ID)
        assert len(result.incomes) == 2
        assert result.statistics.count == 2
        assert result.statistics.total_amount == 300.0

    @pytest.mark.asyncio
    async def test_get_by_category_empty(self, income_service):
        result = await income_service.get_by_category(999, TEST_USER_ID, TEST_WORKSPACE_ID)
        assert len(result.incomes) == 0
        assert result.statistics.count == 0
        assert result.statistics.average_amount == 0.0


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
class TestIncomeServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_amount(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=100.0)
        update = IncomeUpdate(amount=250.0)
        result = await income_service.update(income.id, update, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.amount == 250.0

    @pytest.mark.asyncio
    async def test_update_description(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=100.0, description="old")
        update = IncomeUpdate(description="new description")
        result = await income_service.update(income.id, update, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.description == "new description"

    @pytest.mark.asyncio
    async def test_update_date(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=100.0)
        update = IncomeUpdate(date="2025-02-01")
        result = await income_service.update(income.id, update, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.date.date() == date(2025, 2, 1)

    @pytest.mark.asyncio
    async def test_update_nonexistent_raises(self, income_service):
        update = IncomeUpdate(amount=200.0)
        with pytest.raises(IncomeNotFoundError):
            await income_service.update(99999, update, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_update_negative_amount_raises(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=100.0)
        # Pydantic rejects negative amounts, so use MagicMock to bypass schema validation
        update = MagicMock()
        update.amount = -10.0
        update.date = None
        update.description = None
        update.category_id = None
        update.account_id = None
        update.currency = None

        with pytest.raises(IncomeAmountError):
            await income_service.update(income.id, update, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_update_amount_too_large_raises(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=100.0)
        update = MagicMock()
        update.amount = 1_000_000.0
        update.date = None
        update.description = None
        update.category_id = None
        update.account_id = None
        update.currency = None

        with pytest.raises(IncomeAmountError):
            await income_service.update(income.id, update, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_update_invalid_date_raises(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=100.0)
        update = IncomeUpdate(date="invalid-date")

        with pytest.raises(IncomeDateError):
            await income_service.update(income.id, update, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_update_future_date_raises(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=100.0)
        future = (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%d")
        update = IncomeUpdate(date=future)

        with pytest.raises(IncomeDateError):
            await income_service.update(income.id, update, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_update_long_description_raises(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=100.0)
        update = MagicMock()
        update.amount = None
        update.date = None
        update.description = "x" * 501
        update.category_id = None
        update.account_id = None
        update.currency = None

        with pytest.raises(IncomeDescriptionError):
            await income_service.update(income.id, update, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_update_category_validates(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=100.0)
        update = IncomeUpdate(category_id=5)
        result = await income_service.update(income.id, update, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.category_id == 5
        income_service.category_client.validate_category.assert_called()

    @pytest.mark.asyncio
    async def test_update_currency(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=100.0, currency="USD")
        update = IncomeUpdate(currency="EUR")
        result = await income_service.update(income.id, update, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result.currency == "EUR"


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
class TestIncomeServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_success(self, income_service, create_income_in_db):
        income = create_income_in_db(amount=100.0)
        result = await income_service.delete(income.id, TEST_USER_ID, TEST_WORKSPACE_ID)

        assert result is True
        with pytest.raises(IncomeNotFoundError):
            income_service.get_by_id(income.id, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises(self, income_service):
        with pytest.raises(IncomeNotFoundError):
            await income_service.delete(99999, TEST_USER_ID, TEST_WORKSPACE_ID)

    @pytest.mark.asyncio
    async def test_delete_with_account_restores_balance(self, income_service, create_income_in_db, mock_account_client):
        income = create_income_in_db(amount=500.0, account_id=10)
        await income_service.delete(income.id, TEST_USER_ID, TEST_WORKSPACE_ID)

        mock_account_client.update_account_balance.assert_called_once()
        call_args = mock_account_client.update_account_balance.call_args
        # Should subtract the amount (negative)
        assert call_args[0][2] == -500.0  # amount_change is negative

    @pytest.mark.asyncio
    async def test_delete_without_account_no_balance_update(self, income_service, create_income_in_db, mock_account_client):
        income = create_income_in_db(amount=500.0, account_id=None)
        await income_service.delete(income.id, TEST_USER_ID, TEST_WORKSPACE_ID)

        mock_account_client.update_account_balance.assert_not_called()


# ---------------------------------------------------------------------------
# SUMMARY & STATS
# ---------------------------------------------------------------------------
class TestIncomeServiceSummary:
    def test_get_summary(self, income_service, create_income_in_db):
        create_income_in_db(amount=100.0, income_date=datetime(2025, 1, 10))
        create_income_in_db(amount=200.0, income_date=datetime(2025, 1, 20))
        create_income_in_db(amount=300.0, income_date=datetime(2025, 2, 15))  # outside range

        result = income_service.get_summary(
            TEST_USER_ID, TEST_WORKSPACE_ID,
            datetime(2025, 1, 1), datetime(2025, 1, 31)
        )
        assert result.total_income == 300.0
        assert result.count == 2
        assert result.average_income == 150.0

    def test_get_summary_no_incomes(self, income_service):
        result = income_service.get_summary(
            TEST_USER_ID, TEST_WORKSPACE_ID,
            datetime(2025, 1, 1), datetime(2025, 1, 31)
        )
        assert result.total_income == 0
        assert result.count == 0
        assert result.average_income == 0


class TestIncomeServiceStats:
    def test_get_stats(self, income_service, create_income_in_db):
        now = datetime.utcnow()
        create_income_in_db(amount=100.0, income_date=now)
        create_income_in_db(amount=200.0, income_date=now - timedelta(days=60))

        result = income_service.get_stats(TEST_USER_ID, TEST_WORKSPACE_ID)
        assert result.total_income == 300.0
        assert result.income_count == 2
        assert result.average_income == 150.0

    def test_get_stats_empty(self, income_service):
        result = income_service.get_stats(TEST_USER_ID, TEST_WORKSPACE_ID)
        assert result.total_income == 0
        assert result.income_count == 0
        assert result.average_income == 0


class TestIncomeServiceCurrentMonthCount:
    def test_get_current_month_count(self, income_service, create_income_in_db):
        create_income_in_db(amount=100.0)
        create_income_in_db(amount=200.0)

        result = income_service.get_current_month_count(TEST_USER_ID, TEST_WORKSPACE_ID)
        assert result["count"] == 2
        assert "limit" in result
