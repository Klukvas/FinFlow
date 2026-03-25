"""
Unit tests for DebtService business logic.

Tests cover:
- Debt CRUD operations
- Payment creation and balance updates
- Debt summary with currency conversion
- Subscription limit enforcement
- Read-only excess enforcement
- Authorization checks
- Error handling
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

from app.services.debt import DebtService
from app.models.debt import Debt, DebtPayment, Contact
from app.schemas.debt import (
    DebtCreate, DebtUpdate, DebtResponse,
    DebtPaymentCreate, DebtType, PaymentMethod,
)
from app.exceptions import (
    DebtNotFoundError,
    DebtCreationFailedError,
    DebtUpdateFailedError,
    DebtDeletionFailedError,
    DebtValidationError,
    DebtLimitExceededError,
    DebtReadOnlyExcessError,
    ContactNotFoundError,
    PaymentCreationFailedError,
)


class TestCreateDebt:
    """Tests for DebtService.create_debt()"""

    def test_create_debt_success(self, debt_service, workspace_id, user_id):
        """Successfully create a debt with all fields."""
        debt_data = DebtCreate(
            name="Test Loan",
            description="A test loan",
            debt_type=DebtType.LOAN,
            currency="USD",
            initial_amount=10000.00,
            interest_rate=5.0,
            minimum_payment=200.00,
            start_date=date(2024, 1, 1),
            due_date=date(2029, 1, 1),
        )

        result = debt_service.create_debt(debt_data, user_id, workspace_id)

        assert result.name == "Test Loan"
        assert result.debt_type == DebtType.LOAN
        assert result.initial_amount == 10000.00
        assert result.current_balance == 10000.00
        assert result.currency == "USD"
        assert result.interest_rate == 5.0
        assert result.is_active is True
        assert result.is_paid_off is False
        assert result.payment_count == 0

    def test_create_debt_with_contact(self, debt_service, workspace_id, user_id, sample_contact):
        """Create a debt with an associated contact."""
        debt_data = DebtCreate(
            name="Credit Card",
            debt_type=DebtType.CREDIT_CARD,
            contact_id=sample_contact.id,
            currency="USD",
            initial_amount=5000.00,
            start_date=date(2024, 1, 1),
        )

        result = debt_service.create_debt(debt_data, user_id, workspace_id)

        assert result.contact_id == sample_contact.id
        assert result.name == "Credit Card"

    def test_create_debt_with_invalid_contact_raises(self, debt_service, workspace_id, user_id):
        """Creating a debt referencing a non-existent contact raises error."""
        debt_data = DebtCreate(
            name="Test Debt",
            debt_type=DebtType.LOAN,
            contact_id=99999,
            currency="USD",
            initial_amount=1000.00,
            start_date=date(2024, 1, 1),
        )

        with pytest.raises(ContactNotFoundError):
            debt_service.create_debt(debt_data, user_id, workspace_id)

    def test_create_debt_subscription_limit_exceeded(self, debt_service, workspace_id, user_id):
        """Raise error when subscription debt limit is exceeded."""
        debt_service.subscription_client.check_limit.return_value = (False, 5)

        debt_data = DebtCreate(
            name="Over Limit Debt",
            debt_type=DebtType.LOAN,
            currency="USD",
            initial_amount=1000.00,
            start_date=date(2024, 1, 1),
        )

        with pytest.raises(DebtLimitExceededError):
            debt_service.create_debt(debt_data, user_id, workspace_id)

    def test_create_debt_without_optional_fields(self, debt_service, workspace_id, user_id):
        """Create a debt with only required fields."""
        debt_data = DebtCreate(
            name="Minimal Debt",
            debt_type=DebtType.OTHER,
            currency="EUR",
            initial_amount=500.00,
            start_date=date(2024, 6, 1),
        )

        result = debt_service.create_debt(debt_data, user_id, workspace_id)

        assert result.name == "Minimal Debt"
        assert result.description is None
        assert result.contact_id is None
        assert result.interest_rate is None
        assert result.minimum_payment is None
        assert result.due_date is None

    def test_create_debt_sets_current_balance_to_initial(self, debt_service, workspace_id, user_id):
        """Current balance should match initial amount for new debts."""
        debt_data = DebtCreate(
            name="Balance Check",
            debt_type=DebtType.PERSONAL_LOAN,
            currency="USD",
            initial_amount=7500.50,
            start_date=date(2024, 1, 1),
        )

        result = debt_service.create_debt(debt_data, user_id, workspace_id)

        assert result.current_balance == 7500.50
        assert result.initial_amount == 7500.50

    def test_create_debt_workspace_authorization_called(self, debt_service, workspace_id, user_id):
        """Verify workspace authorization is called with member role."""
        debt_data = DebtCreate(
            name="Auth Check",
            debt_type=DebtType.LOAN,
            currency="USD",
            initial_amount=1000.00,
            start_date=date(2024, 1, 1),
        )

        debt_service.create_debt(debt_data, user_id, workspace_id)

        debt_service.workspace_client.authorize.assert_called_with(
            workspace_id, user_id, "member"
        )

    def test_create_debt_db_error_raises_creation_failed(self, debt_service, workspace_id, user_id):
        """Database error during creation raises DebtCreationFailedError."""
        debt_data = DebtCreate(
            name="DB Error Debt",
            debt_type=DebtType.LOAN,
            currency="USD",
            initial_amount=1000.00,
            start_date=date(2024, 1, 1),
        )

        # Force a DB error by closing the session
        original_add = debt_service.db.add
        debt_service.db.add = Mock(side_effect=RuntimeError("DB connection lost"))

        with pytest.raises(DebtCreationFailedError):
            debt_service.create_debt(debt_data, user_id, workspace_id)

        debt_service.db.add = original_add


class TestGetDebts:
    """Tests for DebtService.get_debts()"""

    def test_get_debts_returns_all(self, debt_service, workspace_id, user_id, multiple_debts):
        """Get all debts for a workspace."""
        debts = debt_service.get_debts(user_id, workspace_id)

        assert len(debts) == 4

    def test_get_debts_active_only(self, debt_service, workspace_id, user_id, multiple_debts):
        """Filter to only active debts."""
        debts = debt_service.get_debts(user_id, workspace_id, active_only=True)

        assert all(d.is_active for d in debts)
        assert len(debts) == 3

    def test_get_debts_paid_off_only(self, debt_service, workspace_id, user_id, multiple_debts):
        """Filter to only paid-off debts."""
        debts = debt_service.get_debts(user_id, workspace_id, paid_off_only=True)

        assert all(d.is_paid_off for d in debts)
        assert len(debts) == 1

    def test_get_debts_pagination_skip(self, debt_service, workspace_id, user_id, multiple_debts):
        """Skip pagination works correctly."""
        debts = debt_service.get_debts(user_id, workspace_id, skip=2)

        assert len(debts) == 2

    def test_get_debts_pagination_limit(self, debt_service, workspace_id, user_id, multiple_debts):
        """Limit pagination works correctly."""
        debts = debt_service.get_debts(user_id, workspace_id, limit=2)

        assert len(debts) == 2

    def test_get_debts_empty_workspace(self, debt_service, user_id):
        """Return empty list when no debts exist."""
        empty_ws = uuid4()
        debts = debt_service.get_debts(user_id, empty_ws)

        assert debts == []

    def test_get_debts_includes_payment_count(self, debt_service, workspace_id, user_id, sample_debt, sample_payment):
        """Debts include payment count."""
        debts = debt_service.get_debts(user_id, workspace_id)

        debt_with_payment = next(d for d in debts if d.id == sample_debt.id)
        assert debt_with_payment.payment_count == 1


class TestGetDebt:
    """Tests for DebtService.get_debt()"""

    def test_get_debt_success(self, debt_service, workspace_id, user_id, sample_debt):
        """Get a specific debt by ID."""
        result = debt_service.get_debt(sample_debt.id, user_id, workspace_id)

        assert result.id == sample_debt.id
        assert result.name == "Credit Card - Visa"

    def test_get_debt_not_found(self, debt_service, workspace_id, user_id):
        """Raise error when debt does not exist."""
        with pytest.raises(DebtNotFoundError):
            debt_service.get_debt(99999, user_id, workspace_id)

    def test_get_debt_wrong_workspace(self, debt_service, user_id, sample_debt):
        """Raise error when debt belongs to different workspace."""
        other_ws = uuid4()
        with pytest.raises(DebtNotFoundError):
            debt_service.get_debt(sample_debt.id, user_id, other_ws)

    def test_get_debt_wrong_user(self, debt_service, workspace_id, sample_debt):
        """Raise error when debt belongs to different user."""
        with pytest.raises(DebtNotFoundError):
            debt_service.get_debt(sample_debt.id, 99999, workspace_id)

    def test_get_debt_includes_contact(self, debt_service, workspace_id, user_id, sample_debt, sample_contact):
        """Debt response includes contact info."""
        result = debt_service.get_debt(sample_debt.id, user_id, workspace_id)

        assert result.contact is not None
        assert result.contact.name == "John Smith"

    def test_get_debt_includes_payment_count(self, debt_service, workspace_id, user_id, sample_debt, sample_payment):
        """Debt response includes correct payment count."""
        result = debt_service.get_debt(sample_debt.id, user_id, workspace_id)

        assert result.payment_count == 1


class TestUpdateDebt:
    """Tests for DebtService.update_debt()"""

    def test_update_debt_name(self, debt_service, workspace_id, user_id, sample_debt):
        """Update debt name."""
        update = DebtUpdate(name="Updated Name")

        result = debt_service.update_debt(sample_debt.id, update, user_id, workspace_id)

        assert result.name == "Updated Name"

    def test_update_debt_multiple_fields(self, debt_service, workspace_id, user_id, sample_debt):
        """Update multiple debt fields at once."""
        update = DebtUpdate(
            name="New Name",
            description="New description",
            interest_rate=15.5,
            minimum_payment=200.00,
        )

        result = debt_service.update_debt(sample_debt.id, update, user_id, workspace_id)

        assert result.name == "New Name"
        assert result.description == "New description"
        assert result.interest_rate == 15.5

    def test_update_debt_not_found(self, debt_service, workspace_id, user_id):
        """Raise error when updating non-existent debt."""
        update = DebtUpdate(name="Does Not Exist")

        with pytest.raises(DebtNotFoundError):
            debt_service.update_debt(99999, update, user_id, workspace_id)

    def test_update_debt_type(self, debt_service, workspace_id, user_id, sample_debt):
        """Update debt type."""
        update = DebtUpdate(debt_type=DebtType.PERSONAL_LOAN)

        result = debt_service.update_debt(sample_debt.id, update, user_id, workspace_id)

        assert result.debt_type == DebtType.PERSONAL_LOAN

    def test_update_debt_currency_with_payments_raises(
        self, debt_service, workspace_id, user_id, sample_debt, sample_payment
    ):
        """Cannot change currency when debt has payments."""
        update = DebtUpdate(currency="EUR")

        with pytest.raises(DebtValidationError) as exc_info:
            debt_service.update_debt(sample_debt.id, update, user_id, workspace_id)

        assert "Cannot change currency" in str(exc_info.value.message)

    def test_update_debt_currency_without_payments(self, debt_service, workspace_id, user_id, sample_debt_no_contact):
        """Can change currency when debt has no payments."""
        update = DebtUpdate(currency="EUR")

        result = debt_service.update_debt(sample_debt_no_contact.id, update, user_id, workspace_id)

        assert result.currency == "EUR"

    def test_update_debt_read_only_raises(self, debt_service, workspace_id, user_id, sample_debt):
        """Raise error when modifying a read-only debt (excess)."""
        debt_service.subscription_client.check_modify_allowed.return_value = False
        debt_service.subscription_client.get_user_features.return_value = {
            "debts": {"limit_value": 1}
        }

        update = DebtUpdate(name="Cannot Edit")

        with pytest.raises(DebtReadOnlyExcessError):
            debt_service.update_debt(sample_debt.id, update, user_id, workspace_id)

    def test_update_debt_paid_off_sets_inactive(self, debt_service, workspace_id, user_id, db_session):
        """Setting current_balance to 0 marks debt as paid off."""
        debt = Debt(
            user_id=user_id,
            workspace_id=workspace_id,
            name="Almost Paid",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("100.00"),
            current_balance=Decimal("0.00"),
            start_date=date(2024, 1, 1),
            is_active=True,
            is_paid_off=False,
        )
        db_session.add(debt)
        db_session.commit()
        db_session.refresh(debt)

        update = DebtUpdate(name="Fully Paid")

        result = debt_service.update_debt(debt.id, update, user_id, workspace_id)

        assert result.is_paid_off is True
        assert result.is_active is False


class TestDeleteDebt:
    """Tests for DebtService.delete_debt()"""

    def test_delete_debt_success(self, debt_service, workspace_id, user_id, sample_debt):
        """Successfully delete a debt."""
        result = debt_service.delete_debt(sample_debt.id, user_id, workspace_id)

        assert result is True

        # Verify debt is gone
        with pytest.raises(DebtNotFoundError):
            debt_service.get_debt(sample_debt.id, user_id, workspace_id)

    def test_delete_debt_with_payments(self, debt_service, workspace_id, user_id, sample_debt, sample_payment):
        """Deleting a debt also deletes associated payments."""
        result = debt_service.delete_debt(sample_debt.id, user_id, workspace_id)

        assert result is True

        # Verify payments are deleted
        remaining_payments = debt_service.db.query(DebtPayment).filter(
            DebtPayment.debt_id == sample_debt.id
        ).count()
        assert remaining_payments == 0

    def test_delete_debt_not_found(self, debt_service, workspace_id, user_id):
        """Raise error when deleting non-existent debt."""
        with pytest.raises(DebtNotFoundError):
            debt_service.delete_debt(99999, user_id, workspace_id)

    def test_delete_debt_wrong_workspace(self, debt_service, user_id, sample_debt):
        """Raise error when debt belongs to different workspace."""
        other_ws = uuid4()
        with pytest.raises(DebtNotFoundError):
            debt_service.delete_debt(sample_debt.id, user_id, other_ws)


class TestCreatePayment:
    """Tests for DebtService.create_payment()"""

    def test_create_payment_success(self, debt_service, workspace_id, user_id, sample_debt):
        """Successfully create a payment."""
        payment_data = DebtPaymentCreate(
            amount=200.00,
            principal_amount=150.00,
            interest_amount=50.00,
            payment_date=date(2024, 3, 1),
            description="March payment",
            payment_method=PaymentMethod.TRANSFER,
        )

        result = debt_service.create_payment(sample_debt.id, payment_data, user_id, workspace_id)

        assert result.amount == 200.00
        assert result.principal_amount == 150.00
        assert result.interest_amount == 50.00
        assert result.debt_id == sample_debt.id
        assert result.user_id == user_id

    def test_create_payment_reduces_balance(self, debt_service, workspace_id, user_id, sample_debt):
        """Payment reduces the debt's current balance by principal amount."""
        initial_balance = float(sample_debt.current_balance)

        payment_data = DebtPaymentCreate(
            amount=500.00,
            principal_amount=400.00,
            interest_amount=100.00,
            payment_date=date(2024, 3, 1),
        )

        debt_service.create_payment(sample_debt.id, payment_data, user_id, workspace_id)

        # Refresh and check balance
        debt_service.db.refresh(sample_debt)
        expected_balance = initial_balance - 400.00
        assert float(sample_debt.current_balance) == expected_balance

    def test_create_payment_uses_amount_when_no_principal(self, debt_service, workspace_id, user_id, sample_debt):
        """When principal_amount is None, full amount reduces balance."""
        initial_balance = float(sample_debt.current_balance)

        payment_data = DebtPaymentCreate(
            amount=300.00,
            payment_date=date(2024, 3, 1),
        )

        debt_service.create_payment(sample_debt.id, payment_data, user_id, workspace_id)

        debt_service.db.refresh(sample_debt)
        expected_balance = initial_balance - 300.00
        assert float(sample_debt.current_balance) == expected_balance

    def test_create_payment_overpayment_sets_zero_balance(self, debt_service, workspace_id, user_id, db_session):
        """Overpayment sets balance to zero and marks debt as paid off."""
        debt = Debt(
            user_id=user_id,
            workspace_id=workspace_id,
            name="Small Debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("100.00"),
            current_balance=Decimal("50.00"),
            start_date=date(2024, 1, 1),
            is_active=True,
            is_paid_off=False,
        )
        db_session.add(debt)
        db_session.commit()
        db_session.refresh(debt)

        payment_data = DebtPaymentCreate(
            amount=100.00,
            payment_date=date(2024, 3, 1),
        )

        debt_service.create_payment(debt.id, payment_data, user_id, workspace_id)

        db_session.refresh(debt)
        assert float(debt.current_balance) == 0.0
        assert debt.is_paid_off is True
        assert debt.is_active is False

    def test_create_payment_updates_last_payment_date(self, debt_service, workspace_id, user_id, sample_debt):
        """Payment updates the debt's last_payment_date."""
        payment_date = date(2024, 5, 15)
        payment_data = DebtPaymentCreate(
            amount=100.00,
            payment_date=payment_date,
        )

        debt_service.create_payment(sample_debt.id, payment_data, user_id, workspace_id)

        debt_service.db.refresh(sample_debt)
        assert sample_debt.last_payment_date == payment_date

    def test_create_payment_debt_not_found(self, debt_service, workspace_id, user_id):
        """Raise error when paying a non-existent debt."""
        payment_data = DebtPaymentCreate(
            amount=100.00,
            payment_date=date(2024, 3, 1),
        )

        with pytest.raises(DebtNotFoundError):
            debt_service.create_payment(99999, payment_data, user_id, workspace_id)

    def test_create_payment_with_method(self, debt_service, workspace_id, user_id, sample_debt):
        """Create payment with a specific payment method."""
        payment_data = DebtPaymentCreate(
            amount=100.00,
            payment_date=date(2024, 3, 1),
            payment_method=PaymentMethod.CASH,
        )

        result = debt_service.create_payment(sample_debt.id, payment_data, user_id, workspace_id)

        assert result.payment_method == PaymentMethod.CASH


class TestGetPayments:
    """Tests for DebtService.get_payments()"""

    def test_get_payments_success(self, debt_service, user_id, sample_debt, sample_payment):
        """Get payments for a debt."""
        payments = debt_service.get_payments(sample_debt.id, user_id)

        assert len(payments) == 1
        assert payments[0].id == sample_payment.id
        assert payments[0].amount == 200.00

    def test_get_payments_empty(self, debt_service, user_id, sample_debt):
        """Return empty list when no payments exist."""
        payments = debt_service.get_payments(sample_debt.id, user_id)

        assert payments == []

    def test_get_payments_pagination(self, debt_service, workspace_id, user_id, sample_debt, db_session):
        """Pagination works for payments."""
        for i in range(5):
            payment = DebtPayment(
                debt_id=sample_debt.id,
                user_id=user_id,
                amount=Decimal(f"{(i + 1) * 100}.00"),
                payment_date=date(2024, i + 1, 1),
            )
            db_session.add(payment)
        db_session.commit()

        all_payments = debt_service.get_payments(sample_debt.id, user_id)
        assert len(all_payments) == 5

        limited = debt_service.get_payments(sample_debt.id, user_id, limit=3)
        assert len(limited) == 3

        skipped = debt_service.get_payments(sample_debt.id, user_id, skip=2)
        assert len(skipped) == 3

    def test_get_payments_ordered_by_date_desc(self, debt_service, user_id, sample_debt, db_session):
        """Payments are ordered by date descending."""
        dates = [date(2024, 1, 1), date(2024, 6, 1), date(2024, 3, 1)]
        for d in dates:
            payment = DebtPayment(
                debt_id=sample_debt.id,
                user_id=user_id,
                amount=Decimal("100.00"),
                payment_date=d,
            )
            db_session.add(payment)
        db_session.commit()

        payments = debt_service.get_payments(sample_debt.id, user_id)

        payment_dates = [p.payment_date for p in payments]
        assert payment_dates == sorted(payment_dates, reverse=True)


class TestGetDebtSummary:
    """Tests for DebtService.get_debt_summary()"""

    def test_get_summary_with_debts(self, debt_service, workspace_id, user_id, multiple_debts):
        """Get summary with multiple debts."""
        result = debt_service.get_debt_summary(user_id, workspace_id)

        assert result.active_debts == 3
        assert result.paid_off_debts == 1
        assert result.currency == "USD"
        assert result.total_debt > 0

    def test_get_summary_empty_workspace(self, debt_service, user_id):
        """Summary for workspace with no debts."""
        empty_ws = uuid4()
        result = debt_service.get_debt_summary(user_id, empty_ws)

        assert result.total_debt == 0.0
        assert result.total_payments == 0.0
        assert result.active_debts == 0
        assert result.paid_off_debts == 0
        assert result.average_interest_rate is None

    def test_get_summary_uses_user_currency(self, debt_service, workspace_id, user_id, multiple_debts):
        """Summary uses user's base currency."""
        debt_service.user_client.get_user_base_currency.return_value = "EUR"

        result = debt_service.get_debt_summary(user_id, workspace_id)

        assert result.currency == "EUR"
        debt_service.user_client.get_user_base_currency.assert_called_with(user_id)

    def test_get_summary_fallback_currency_on_error(self, debt_service, workspace_id, user_id, multiple_debts):
        """Falls back to USD when user service fails."""
        debt_service.user_client.get_user_base_currency.side_effect = Exception("Service unavailable")

        result = debt_service.get_debt_summary(user_id, workspace_id)

        assert result.currency == "USD"

    def test_get_summary_average_interest_rate(self, debt_service, workspace_id, user_id, db_session):
        """Average interest rate is calculated correctly."""
        for rate in [10.0, 20.0, 30.0]:
            debt = Debt(
                user_id=user_id,
                workspace_id=workspace_id,
                name=f"Debt {rate}",
                debt_type="LOAN",
                currency="USD",
                initial_amount=Decimal("1000.00"),
                current_balance=Decimal("1000.00"),
                interest_rate=Decimal(str(rate)),
                start_date=date(2024, 1, 1),
                is_active=True,
                is_paid_off=False,
            )
            db_session.add(debt)
        db_session.commit()

        result = debt_service.get_debt_summary(user_id, workspace_id)

        assert result.average_interest_rate == pytest.approx(20.0, abs=0.01)

    def test_get_summary_includes_payment_totals(
        self, debt_service, workspace_id, user_id, sample_debt, sample_payment
    ):
        """Summary includes total payments."""
        result = debt_service.get_debt_summary(user_id, workspace_id)

        assert result.total_payments > 0


class TestGetOrderedIds:
    """Tests for DebtService._get_ordered_ids()"""

    def test_ordered_ids_returns_correct_order(self, debt_service, workspace_id, user_id, db_session):
        """IDs are ordered by created_at ascending."""
        debts = []
        for i in range(3):
            debt = Debt(
                user_id=user_id,
                workspace_id=workspace_id,
                name=f"Debt {i}",
                debt_type="LOAN",
                currency="USD",
                initial_amount=Decimal("1000.00"),
                current_balance=Decimal("1000.00"),
                start_date=date(2024, 1, 1),
                is_active=True,
            )
            db_session.add(debt)
            db_session.flush()
            debts.append(debt)
        db_session.commit()

        ordered = debt_service._get_ordered_ids(workspace_id)

        assert len(ordered) == 3
        # IDs should be in ascending order since they are auto-increment
        assert ordered == sorted(ordered)

    def test_ordered_ids_empty_workspace(self, debt_service):
        """Return empty list for workspace with no debts."""
        ordered = debt_service._get_ordered_ids(uuid4())

        assert ordered == []
