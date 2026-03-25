"""
Unit tests for SQLAlchemy models.

Tests cover:
- Model creation and field types
- Relationships between models
- Default values
- Constraints
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from app.models.debt import Debt, Contact, DebtPayment


class TestContactModel:
    """Tests for Contact model."""

    def test_create_contact(self, db_session):
        """Create a contact with all fields."""
        ws_id = uuid4()
        contact = Contact(
            user_id=1,
            workspace_id=str(ws_id),
            name="Test Contact",
            email="test@example.com",
            phone="+1-555-0000",
            company="Test Corp",
            address="123 Test St",
            notes="Test notes",
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        assert contact.id is not None
        assert contact.name == "Test Contact"
        assert contact.email == "test@example.com"
        assert str(contact.workspace_id) == str(ws_id)

    def test_contact_minimal(self, db_session):
        """Create contact with only required fields."""
        contact = Contact(
            user_id=1,
            workspace_id=str(uuid4()),
            name="Minimal",
        )
        db_session.add(contact)
        db_session.commit()
        db_session.refresh(contact)

        assert contact.id is not None
        assert contact.email is None
        assert contact.phone is None

    def test_contact_debts_relationship(self, db_session, sample_contact, sample_debt):
        """Contact has debts relationship."""
        db_session.refresh(sample_contact)

        assert len(sample_contact.debts) == 1
        assert sample_contact.debts[0].name == "Credit Card - Visa"


class TestDebtModel:
    """Tests for Debt model."""

    def test_create_debt(self, db_session):
        """Create a debt with all fields."""
        ws_id = uuid4()
        debt = Debt(
            user_id=1,
            workspace_id=str(ws_id),
            name="Test Debt",
            description="A test debt",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("10000.00"),
            current_balance=Decimal("10000.00"),
            interest_rate=Decimal("5.50"),
            minimum_payment=Decimal("200.00"),
            start_date=date(2024, 1, 1),
            due_date=date(2029, 1, 1),
        )
        db_session.add(debt)
        db_session.commit()
        db_session.refresh(debt)

        assert debt.id is not None
        assert debt.name == "Test Debt"
        assert debt.is_active is True
        assert debt.is_paid_off is False

    def test_debt_default_values(self, db_session):
        """Verify default values for boolean fields."""
        debt = Debt(
            user_id=1,
            workspace_id=str(uuid4()),
            name="Defaults",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("1000.00"),
            current_balance=Decimal("1000.00"),
            start_date=date(2024, 1, 1),
        )
        db_session.add(debt)
        db_session.commit()
        db_session.refresh(debt)

        assert debt.is_active is True
        assert debt.is_paid_off is False

    def test_debt_contact_relationship(self, db_session, sample_debt, sample_contact):
        """Debt has contact relationship."""
        db_session.refresh(sample_debt)

        assert sample_debt.contact is not None
        assert sample_debt.contact.name == "John Smith"

    def test_debt_payments_relationship(self, db_session, sample_debt, sample_payment):
        """Debt has payments relationship."""
        db_session.refresh(sample_debt)

        assert len(sample_debt.payments) == 1
        assert float(sample_debt.payments[0].amount) == 200.00

    def test_debt_without_contact(self, db_session, sample_debt_no_contact):
        """Debt without contact has None contact."""
        db_session.refresh(sample_debt_no_contact)

        assert sample_debt_no_contact.contact is None
        assert sample_debt_no_contact.contact_id is None


class TestDebtPaymentModel:
    """Tests for DebtPayment model."""

    def test_create_payment(self, db_session, sample_debt):
        """Create a payment with all fields."""
        payment = DebtPayment(
            debt_id=sample_debt.id,
            user_id=1,
            amount=Decimal("200.00"),
            principal_amount=Decimal("150.00"),
            interest_amount=Decimal("50.00"),
            payment_date=date(2024, 3, 1),
            description="Test payment",
            payment_method="CASH",
        )
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)

        assert payment.id is not None
        assert float(payment.amount) == 200.00
        assert payment.payment_method == "CASH"

    def test_payment_minimal(self, db_session, sample_debt):
        """Create payment with only required fields."""
        payment = DebtPayment(
            debt_id=sample_debt.id,
            user_id=1,
            amount=Decimal("100.00"),
            payment_date=date(2024, 3, 1),
        )
        db_session.add(payment)
        db_session.commit()
        db_session.refresh(payment)

        assert payment.principal_amount is None
        assert payment.interest_amount is None
        assert payment.description is None
        assert payment.payment_method is None

    def test_payment_debt_relationship(self, db_session, sample_payment, sample_debt):
        """Payment has debt relationship."""
        db_session.refresh(sample_payment)

        assert sample_payment.debt is not None
        assert sample_payment.debt.name == "Credit Card - Visa"

    def test_multiple_payments_for_debt(self, db_session, sample_debt):
        """Multiple payments can be created for a single debt."""
        for i in range(3):
            payment = DebtPayment(
                debt_id=sample_debt.id,
                user_id=1,
                amount=Decimal(f"{(i + 1) * 100}.00"),
                payment_date=date(2024, i + 1, 1),
            )
            db_session.add(payment)
        db_session.commit()

        db_session.refresh(sample_debt)
        assert len(sample_debt.payments) == 3


class TestForeignKeyConstraints:
    """Tests for foreign key constraints."""

    def test_debt_references_valid_contact(self, db_session, sample_contact):
        """Debt can reference an existing contact."""
        debt = Debt(
            user_id=1,
            workspace_id=sample_contact.workspace_id,
            contact_id=sample_contact.id,
            name="FK Test",
            debt_type="LOAN",
            currency="USD",
            initial_amount=Decimal("1000.00"),
            current_balance=Decimal("1000.00"),
            start_date=date(2024, 1, 1),
        )
        db_session.add(debt)
        db_session.commit()

        assert debt.contact_id == sample_contact.id

    def test_payment_references_valid_debt(self, db_session, sample_debt):
        """Payment can reference an existing debt."""
        payment = DebtPayment(
            debt_id=sample_debt.id,
            user_id=1,
            amount=Decimal("50.00"),
            payment_date=date(2024, 3, 1),
        )
        db_session.add(payment)
        db_session.commit()

        assert payment.debt_id == sample_debt.id
