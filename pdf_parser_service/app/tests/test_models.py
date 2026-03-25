"""
Tests for Pydantic models and data validation.

Covers:
- ParsedTransaction: field validation (amount > 0, confidence_score range)
- PDFParseResponse: structure
- BankType and TransactionType enums
- PDFLimitInfo: optional fields
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.models.transaction import (
    ParsedTransaction,
    PDFParseResponse,
    PDFParseRequest,
    PDFLimitInfo,
    BankType,
    TransactionType,
    TransactionValidation,
    BatchCreateRequest,
    BatchCreateResponse,
)


class TestParsedTransaction:

    def test_valid_transaction(self):
        tx = ParsedTransaction(
            amount=100.50,
            description="Test",
            transaction_date=date(2025, 1, 15),
            transaction_type=TransactionType.EXPENSE,
            bank_type=BankType.MONOBANK,
            raw_text="raw",
            confidence_score=0.9,
        )
        assert tx.amount == 100.50
        assert tx.transaction_type == TransactionType.EXPENSE

    def test_amount_must_be_positive(self):
        with pytest.raises(ValidationError) as exc_info:
            ParsedTransaction(
                amount=-10,
                description="Negative",
                transaction_date=date(2025, 1, 1),
                transaction_type=TransactionType.EXPENSE,
                bank_type=BankType.MONOBANK,
                raw_text="",
                confidence_score=0.5,
            )
        assert "Amount must be greater than 0" in str(exc_info.value)

    def test_amount_zero_rejected(self):
        with pytest.raises(ValidationError):
            ParsedTransaction(
                amount=0,
                description="Zero",
                transaction_date=date(2025, 1, 1),
                transaction_type=TransactionType.EXPENSE,
                bank_type=BankType.MONOBANK,
                raw_text="",
                confidence_score=0.5,
            )

    def test_confidence_score_range_low(self):
        with pytest.raises(ValidationError):
            ParsedTransaction(
                amount=10,
                description="Low confidence",
                transaction_date=date(2025, 1, 1),
                transaction_type=TransactionType.EXPENSE,
                bank_type=BankType.MONOBANK,
                raw_text="",
                confidence_score=-0.1,
            )

    def test_confidence_score_range_high(self):
        with pytest.raises(ValidationError):
            ParsedTransaction(
                amount=10,
                description="High confidence",
                transaction_date=date(2025, 1, 1),
                transaction_type=TransactionType.EXPENSE,
                bank_type=BankType.MONOBANK,
                raw_text="",
                confidence_score=1.5,
            )

    def test_optional_fields_default_none(self):
        tx = ParsedTransaction(
            amount=10,
            description="Minimal",
            transaction_date=date(2025, 1, 1),
            transaction_type=TransactionType.INCOME,
            bank_type=BankType.MONOBANK,
            raw_text=None,
            confidence_score=0.7,
        )
        assert tx.mcc_code is None
        assert tx.mcc_category_name is None
        assert tx.category_exists is None
        assert tx.category_id is None


class TestPDFParseResponse:

    def test_valid_response(self):
        tx = ParsedTransaction(
            amount=100,
            description="Test",
            transaction_date=date(2025, 1, 1),
            transaction_type=TransactionType.EXPENSE,
            bank_type=BankType.MONOBANK,
            raw_text="",
            confidence_score=0.8,
        )
        resp = PDFParseResponse(
            transactions=[tx],
            bank_detected=BankType.MONOBANK,
            total_transactions=1,
            successful_parses=1,
            failed_parses=0,
        )
        assert resp.total_transactions == 1
        assert resp.limit_info is None

    def test_empty_transactions(self):
        resp = PDFParseResponse(
            transactions=[],
            bank_detected=BankType.PRIVATBANK,
            total_transactions=0,
            successful_parses=0,
            failed_parses=0,
        )
        assert resp.transactions == []

    def test_with_limit_info(self):
        resp = PDFParseResponse(
            transactions=[],
            bank_detected=BankType.MONOBANK,
            total_transactions=0,
            successful_parses=0,
            failed_parses=0,
            limit_info=PDFLimitInfo(
                uploads_per_month=10,
                records_per_upload=100,
                uploads_used_this_month=1,
                uploads_remaining=9,
                plan_code="professional",
            ),
        )
        assert resp.limit_info.uploads_per_month == 10


class TestPDFLimitInfo:

    def test_all_fields(self):
        info = PDFLimitInfo(
            uploads_per_month=10,
            records_per_upload=100,
            uploads_used_this_month=3,
            uploads_remaining=7,
            plan_code="professional",
        )
        assert info.uploads_remaining == 7

    def test_unlimited_plan(self):
        info = PDFLimitInfo(
            uploads_per_month=None,
            records_per_upload=None,
            uploads_used_this_month=50,
            uploads_remaining=None,
            plan_code="enterprise",
        )
        assert info.uploads_per_month is None


class TestEnums:

    def test_bank_type_values(self):
        assert BankType.MONOBANK.value == "monobank"
        assert BankType.PRIVATBANK.value == "privatbank"
        assert BankType.UKRSIBBANK.value == "ukrsibbank"
        assert BankType.ABANK.value == "abank"
        assert BankType.DEEL.value == "deel"

    def test_transaction_type_values(self):
        assert TransactionType.INCOME.value == "income"
        assert TransactionType.EXPENSE.value == "expense"

    def test_bank_type_from_string(self):
        assert BankType("monobank") == BankType.MONOBANK

    def test_invalid_bank_type_raises(self):
        with pytest.raises(ValueError):
            BankType("nonexistent")


class TestPDFParseRequest:

    def test_valid_request(self):
        req = PDFParseRequest(user_id=42)
        assert req.user_id == 42
        assert req.bank_type is None

    def test_request_with_bank_type(self):
        req = PDFParseRequest(user_id=1, bank_type=BankType.MONOBANK)
        assert req.bank_type == BankType.MONOBANK


class TestTransactionValidation:

    def test_valid_validation(self):
        tv = TransactionValidation(
            transaction_id="tx-001",
            amount=100.0,
            description="Test",
            transaction_date=date(2025, 1, 1),
            transaction_type=TransactionType.EXPENSE,
        )
        assert tv.is_valid is True
        assert tv.category_id is None


class TestBatchCreateRequest:

    def test_valid_batch(self):
        tv = TransactionValidation(
            transaction_id="tx-001",
            amount=100.0,
            description="Test",
            transaction_date=date(2025, 1, 1),
            transaction_type=TransactionType.EXPENSE,
        )
        req = BatchCreateRequest(transactions=[tv], user_id=42)
        assert len(req.transactions) == 1


class TestBatchCreateResponse:

    def test_valid_response(self):
        resp = BatchCreateResponse(
            created_income_count=2,
            created_expense_count=3,
            success=True,
        )
        assert resp.created_income_count == 2
        assert resp.failed_transactions == []
