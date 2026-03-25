"""
Unit tests for Pydantic schemas (input validation).

Tests cover:
- DebtCreate, DebtUpdate validation
- DebtPaymentCreate validation
- ContactCreate, ContactUpdate validation
- Debt type normalization
- Amount rounding and validation
- Edge cases
"""
import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.debt import (
    DebtCreate, DebtUpdate, DebtType, PaymentMethod,
    DebtPaymentCreate,
)
from app.schemas.contact import ContactCreate, ContactUpdate
from app.schemas.error import ErrorResponse


class TestDebtCreateSchema:
    """Tests for DebtCreate schema validation."""

    def test_valid_debt_create(self):
        """Accept valid debt creation data."""
        debt = DebtCreate(
            name="Test Loan",
            debt_type=DebtType.LOAN,
            currency="USD",
            initial_amount=10000.00,
            start_date=date(2024, 1, 1),
        )

        assert debt.name == "Test Loan"
        assert debt.debt_type == DebtType.LOAN
        assert debt.currency == "USD"

    def test_valid_debt_create_all_fields(self):
        """Accept debt with all optional fields."""
        debt = DebtCreate(
            name="Full Debt",
            description="Full description",
            debt_type=DebtType.MORTGAGE,
            contact_id=1,
            category_id=5,
            currency="EUR",
            initial_amount=200000.00,
            interest_rate=3.5,
            minimum_payment=1500.00,
            start_date=date(2024, 1, 1),
            due_date=date(2054, 1, 1),
        )

        assert debt.description == "Full description"
        assert debt.contact_id == 1
        assert debt.category_id == 5
        assert debt.interest_rate == 3.5

    def test_debt_type_normalization_alias(self):
        """Debt type aliases are normalized."""
        debt = DebtCreate(
            name="Alias Test",
            debt_type="PERSONAL",  # type: ignore
            currency="USD",
            initial_amount=1000.00,
            start_date=date(2024, 1, 1),
        )

        assert debt.debt_type == DebtType.PERSONAL_LOAN

    def test_debt_type_normalization_auto(self):
        """AUTO alias normalized to AUTO_LOAN."""
        debt = DebtCreate(
            name="Auto Test",
            debt_type="AUTO",  # type: ignore
            currency="USD",
            initial_amount=15000.00,
            start_date=date(2024, 1, 1),
        )

        assert debt.debt_type == DebtType.AUTO_LOAN

    def test_debt_type_normalization_student(self):
        """STUDENT alias normalized to STUDENT_LOAN."""
        debt = DebtCreate(
            name="Student Test",
            debt_type="STUDENT",  # type: ignore
            currency="USD",
            initial_amount=20000.00,
            start_date=date(2024, 1, 1),
        )

        assert debt.debt_type == DebtType.STUDENT_LOAN

    def test_debt_type_normalization_credit(self):
        """CREDIT alias normalized to CREDIT_CARD."""
        debt = DebtCreate(
            name="Credit Test",
            debt_type="CREDIT",  # type: ignore
            currency="USD",
            initial_amount=5000.00,
            start_date=date(2024, 1, 1),
        )

        assert debt.debt_type == DebtType.CREDIT_CARD

    def test_debt_type_case_insensitive(self):
        """Debt type accepts lowercase."""
        debt = DebtCreate(
            name="Case Test",
            debt_type="loan",  # type: ignore
            currency="USD",
            initial_amount=1000.00,
            start_date=date(2024, 1, 1),
        )

        assert debt.debt_type == DebtType.LOAN

    def test_reject_empty_name(self):
        """Reject empty name."""
        with pytest.raises(ValidationError):
            DebtCreate(
                name="",
                debt_type=DebtType.LOAN,
                currency="USD",
                initial_amount=1000.00,
                start_date=date(2024, 1, 1),
            )

    def test_reject_name_too_long(self):
        """Reject name longer than 255 chars."""
        with pytest.raises(ValidationError):
            DebtCreate(
                name="x" * 256,
                debt_type=DebtType.LOAN,
                currency="USD",
                initial_amount=1000.00,
                start_date=date(2024, 1, 1),
            )

    def test_reject_negative_amount(self):
        """Reject negative initial amount."""
        with pytest.raises(ValidationError):
            DebtCreate(
                name="Negative",
                debt_type=DebtType.LOAN,
                currency="USD",
                initial_amount=-500.00,
                start_date=date(2024, 1, 1),
            )

    def test_reject_zero_amount(self):
        """Reject zero initial amount."""
        with pytest.raises(ValidationError):
            DebtCreate(
                name="Zero",
                debt_type=DebtType.LOAN,
                currency="USD",
                initial_amount=0,
                start_date=date(2024, 1, 1),
            )

    def test_amount_rounded_to_cents(self):
        """Amount is rounded to 2 decimal places."""
        debt = DebtCreate(
            name="Round Test",
            debt_type=DebtType.LOAN,
            currency="USD",
            initial_amount=1234.567,
            start_date=date(2024, 1, 1),
        )

        assert debt.initial_amount == 1234.57

    def test_reject_interest_rate_over_100(self):
        """Reject interest rate over 100%."""
        with pytest.raises(ValidationError):
            DebtCreate(
                name="High Rate",
                debt_type=DebtType.LOAN,
                currency="USD",
                initial_amount=1000.00,
                interest_rate=101.0,
                start_date=date(2024, 1, 1),
            )

    def test_reject_negative_interest_rate(self):
        """Reject negative interest rate."""
        with pytest.raises(ValidationError):
            DebtCreate(
                name="Neg Rate",
                debt_type=DebtType.LOAN,
                currency="USD",
                initial_amount=1000.00,
                interest_rate=-1.0,
                start_date=date(2024, 1, 1),
            )

    def test_accept_zero_interest_rate(self):
        """Accept zero interest rate."""
        debt = DebtCreate(
            name="Zero Rate",
            debt_type=DebtType.LOAN,
            currency="USD",
            initial_amount=1000.00,
            interest_rate=0.0,
            start_date=date(2024, 1, 1),
        )

        assert debt.interest_rate == 0.0

    def test_reject_short_currency(self):
        """Reject currency code shorter than 3 chars."""
        with pytest.raises(ValidationError):
            DebtCreate(
                name="Short Currency",
                debt_type=DebtType.LOAN,
                currency="US",
                initial_amount=1000.00,
                start_date=date(2024, 1, 1),
            )

    def test_reject_long_currency(self):
        """Reject currency code longer than 3 chars."""
        with pytest.raises(ValidationError):
            DebtCreate(
                name="Long Currency",
                debt_type=DebtType.LOAN,
                currency="USDX",
                initial_amount=1000.00,
                start_date=date(2024, 1, 1),
            )

    def test_reject_invalid_debt_type(self):
        """Reject invalid debt type string."""
        with pytest.raises(ValidationError):
            DebtCreate(
                name="Bad Type",
                debt_type="IMAGINARY",  # type: ignore
                currency="USD",
                initial_amount=1000.00,
                start_date=date(2024, 1, 1),
            )

    def test_reject_negative_category_id(self):
        """Reject negative category ID."""
        with pytest.raises(ValidationError):
            DebtCreate(
                name="Bad Category",
                debt_type=DebtType.LOAN,
                currency="USD",
                initial_amount=1000.00,
                category_id=-1,
                start_date=date(2024, 1, 1),
            )

    def test_reject_zero_category_id(self):
        """Reject zero category ID."""
        with pytest.raises(ValidationError):
            DebtCreate(
                name="Bad Category",
                debt_type=DebtType.LOAN,
                currency="USD",
                initial_amount=1000.00,
                category_id=0,
                start_date=date(2024, 1, 1),
            )


class TestDebtUpdateSchema:
    """Tests for DebtUpdate schema validation."""

    def test_valid_partial_update(self):
        """Accept partial update."""
        update = DebtUpdate(name="New Name")

        assert update.name == "New Name"
        assert update.debt_type is None

    def test_all_fields_none_by_default(self):
        """All fields are None when not provided."""
        update = DebtUpdate()

        assert update.name is None
        assert update.debt_type is None
        assert update.interest_rate is None

    def test_debt_type_normalization_in_update(self):
        """Debt type aliases normalized in updates too."""
        update = DebtUpdate(debt_type="PERSONAL")  # type: ignore

        assert update.debt_type == DebtType.PERSONAL_LOAN

    def test_reject_empty_name(self):
        """Reject empty name on update."""
        with pytest.raises(ValidationError):
            DebtUpdate(name="")

    def test_reject_invalid_interest_rate(self):
        """Reject invalid interest rate on update."""
        with pytest.raises(ValidationError):
            DebtUpdate(interest_rate=150.0)


class TestDebtPaymentCreateSchema:
    """Tests for DebtPaymentCreate schema validation."""

    def test_valid_payment(self):
        """Accept valid payment data."""
        payment = DebtPaymentCreate(
            amount=200.00,
            principal_amount=150.00,
            interest_amount=50.00,
            payment_date=date(2024, 3, 1),
            description="Monthly payment",
            payment_method=PaymentMethod.TRANSFER,
        )

        assert payment.amount == 200.00
        assert payment.payment_method == PaymentMethod.TRANSFER

    def test_minimal_payment(self):
        """Accept payment with only required fields."""
        payment = DebtPaymentCreate(
            amount=100.00,
            payment_date=date(2024, 3, 1),
        )

        assert payment.amount == 100.00
        assert payment.principal_amount is None
        assert payment.interest_amount is None
        assert payment.payment_method is None

    def test_reject_negative_amount(self):
        """Reject negative payment amount."""
        with pytest.raises(ValidationError):
            DebtPaymentCreate(
                amount=-100.00,
                payment_date=date(2024, 3, 1),
            )

    def test_reject_zero_amount(self):
        """Reject zero payment amount."""
        with pytest.raises(ValidationError):
            DebtPaymentCreate(
                amount=0,
                payment_date=date(2024, 3, 1),
            )

    def test_amount_rounded_to_cents(self):
        """Payment amount rounded to 2 decimal places."""
        payment = DebtPaymentCreate(
            amount=99.999,
            payment_date=date(2024, 3, 1),
        )

        assert payment.amount == 100.0

    def test_all_payment_methods(self):
        """All payment methods are valid."""
        for method in PaymentMethod:
            payment = DebtPaymentCreate(
                amount=100.00,
                payment_date=date(2024, 3, 1),
                payment_method=method,
            )
            assert payment.payment_method == method

    def test_reject_invalid_payment_method(self):
        """Reject invalid payment method."""
        with pytest.raises(ValidationError):
            DebtPaymentCreate(
                amount=100.00,
                payment_date=date(2024, 3, 1),
                payment_method="BITCOIN",  # type: ignore
            )

    def test_description_max_length(self):
        """Reject description exceeding 500 characters."""
        with pytest.raises(ValidationError):
            DebtPaymentCreate(
                amount=100.00,
                payment_date=date(2024, 3, 1),
                description="x" * 501,
            )


class TestContactCreateSchema:
    """Tests for ContactCreate schema validation."""

    def test_valid_contact(self):
        """Accept valid contact data."""
        contact = ContactCreate(
            name="John Smith",
            email="john@example.com",
            phone="+1-555-0123",
            company="Big Bank",
            address="123 Main St",
            notes="Important contact",
        )

        assert contact.name == "John Smith"
        assert contact.email == "john@example.com"

    def test_minimal_contact(self):
        """Accept contact with only name."""
        contact = ContactCreate(name="Minimal")

        assert contact.name == "Minimal"
        assert contact.email is None

    def test_reject_empty_name(self):
        """Reject empty contact name."""
        with pytest.raises(ValidationError):
            ContactCreate(name="")

    def test_reject_name_too_long(self):
        """Reject name exceeding 255 characters."""
        with pytest.raises(ValidationError):
            ContactCreate(name="x" * 256)

    def test_reject_email_too_long(self):
        """Reject email exceeding 255 characters."""
        with pytest.raises(ValidationError):
            ContactCreate(name="Test", email="x" * 256)

    def test_reject_phone_too_long(self):
        """Reject phone exceeding 50 characters."""
        with pytest.raises(ValidationError):
            ContactCreate(name="Test", phone="x" * 51)


class TestContactUpdateSchema:
    """Tests for ContactUpdate schema validation."""

    def test_partial_update(self):
        """Accept partial update with one field."""
        update = ContactUpdate(name="New Name")

        assert update.name == "New Name"
        assert update.email is None

    def test_empty_update(self):
        """Accept empty update (no changes)."""
        update = ContactUpdate()

        assert update.name is None

    def test_reject_empty_name(self):
        """Reject empty name on update."""
        with pytest.raises(ValidationError):
            ContactUpdate(name="")


class TestErrorResponseSchema:
    """Tests for ErrorResponse schema."""

    def test_error_response_basic(self):
        """Create error response with required fields."""
        error = ErrorResponse(
            error="Something went wrong",
            errorCode="TEST_ERROR",
        )

        assert error.error == "Something went wrong"
        assert error.errorCode == "TEST_ERROR"
        assert error.details is None

    def test_error_response_with_details(self):
        """Create error response with details."""
        error = ErrorResponse(
            error="Validation failed",
            errorCode="VALIDATION_ERROR",
            details={"field": "name", "reason": "too long"},
        )

        assert error.details["field"] == "name"


class TestDebtTypeEnum:
    """Tests for DebtType enum."""

    def test_all_debt_types(self):
        """All expected debt types exist."""
        expected = {
            "CREDIT_CARD", "LOAN", "MORTGAGE",
            "PERSONAL_LOAN", "AUTO_LOAN", "STUDENT_LOAN", "OTHER",
        }
        actual = {dt.value for dt in DebtType}
        assert actual == expected


class TestPaymentMethodEnum:
    """Tests for PaymentMethod enum."""

    def test_all_payment_methods(self):
        """All expected payment methods exist."""
        expected = {"CASH", "CARD", "TRANSFER", "CHECK", "AUTOMATIC", "OTHER"}
        actual = {pm.value for pm in PaymentMethod}
        assert actual == expected
