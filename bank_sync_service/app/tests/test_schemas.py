"""Tests for app/schemas/ - Pydantic schema validation."""

import pytest
from decimal import Decimal
from datetime import datetime, date
from pydantic import ValidationError

from app.schemas.connection import (
    ConnectionCreate,
    ConnectionResponse,
    LinkedAccountResponse,
    LinkAccountRequest,
)
from app.schemas.sync import (
    SyncRequest,
    SyncPreviewRequest,
    SyncPreviewTransaction,
    SyncPreviewResponse,
    SyncConfirmTransaction,
    SyncConfirmRequest,
    SyncStatusResponse,
)
from app.schemas.error import ErrorResponse
from app.schemas.monobank import (
    MonobankAccount,
    MonobankClientInfo,
    MonobankStatementItem,
)


class TestConnectionCreate:
    def test_valid_token(self):
        schema = ConnectionCreate(token="my-monobank-token")
        assert schema.token == "my-monobank-token"

    def test_empty_token_rejected(self):
        with pytest.raises(ValidationError):
            ConnectionCreate(token="")

    def test_missing_token_rejected(self):
        with pytest.raises(ValidationError):
            ConnectionCreate()

    def test_token_max_length_exceeded(self):
        with pytest.raises(ValidationError):
            ConnectionCreate(token="x" * 513)

    def test_token_at_max_length(self):
        schema = ConnectionCreate(token="x" * 512)
        assert len(schema.token) == 512


class TestLinkedAccountResponse:
    def test_minimal_fields(self):
        resp = LinkedAccountResponse(id=1, external_account_id="ext1")
        assert resp.id == 1
        assert resp.external_account_id == "ext1"
        assert resp.is_synced is True
        assert resp.finflow_account_id is None

    def test_all_fields(self):
        resp = LinkedAccountResponse(
            id=1,
            external_account_id="ext1",
            account_name="UAH Card",
            currency="UAH",
            currency_code=980,
            masked_pan="*1234",
            iban="UA123456",
            finflow_account_id=42,
            is_synced=False,
        )
        assert resp.currency == "UAH"
        assert resp.is_synced is False


class TestConnectionResponse:
    def test_minimal_fields(self):
        resp = ConnectionResponse(id=1, bank_type="monobank", is_active=True)
        assert resp.bank_type == "monobank"
        assert resp.accounts == []

    def test_with_accounts(self):
        acc = LinkedAccountResponse(id=1, external_account_id="ext1")
        resp = ConnectionResponse(
            id=1, bank_type="monobank", is_active=True, accounts=[acc]
        )
        assert len(resp.accounts) == 1


class TestLinkAccountRequest:
    def test_valid_request(self):
        req = LinkAccountRequest(finflow_account_id=5)
        assert req.finflow_account_id == 5

    def test_missing_finflow_account_id(self):
        with pytest.raises(ValidationError):
            LinkAccountRequest()


class TestSyncRequest:
    def test_defaults(self):
        req = SyncRequest()
        assert req.account_ids is None
        assert req.days_back == 30

    def test_custom_days_back(self):
        req = SyncRequest(days_back=7)
        assert req.days_back == 7

    def test_days_back_min_violation(self):
        with pytest.raises(ValidationError):
            SyncRequest(days_back=0)

    def test_days_back_max_violation(self):
        with pytest.raises(ValidationError):
            SyncRequest(days_back=31)

    def test_with_account_ids(self):
        req = SyncRequest(account_ids=[1, 2, 3])
        assert req.account_ids == [1, 2, 3]


class TestSyncPreviewRequest:
    def test_defaults(self):
        req = SyncPreviewRequest()
        assert req.days_back == 30

    def test_days_back_boundaries(self):
        req = SyncPreviewRequest(days_back=1)
        assert req.days_back == 1

        req = SyncPreviewRequest(days_back=30)
        assert req.days_back == 30


class TestSyncPreviewTransaction:
    def test_valid(self):
        txn = SyncPreviewTransaction(
            external_id="ext1",
            type="expense",
            amount=Decimal("50.00"),
            currency="UAH",
            date=date(2024, 1, 15),
            description="Shop",
            account_id=1,
        )
        assert txn.type == "expense"

    def test_optional_fields(self):
        txn = SyncPreviewTransaction(
            external_id="ext1",
            type="income",
            amount=Decimal("100.00"),
            currency="USD",
            date=date(2024, 1, 15),
            description="Salary",
            account_id=1,
            mcc=5411,
            category_id=10,
            category_name="Groceries",
        )
        assert txn.mcc == 5411
        assert txn.category_name == "Groceries"


class TestSyncConfirmRequest:
    def test_valid(self):
        txn = SyncConfirmTransaction(
            external_id="ext1",
            type="expense",
            amount=Decimal("25.00"),
            currency="UAH",
            date=date(2024, 1, 15),
            description="Cafe",
            account_id=1,
        )
        req = SyncConfirmRequest(transactions=[txn])
        assert len(req.transactions) == 1
        assert req.days_back == 30

    def test_empty_transactions_allowed(self):
        req = SyncConfirmRequest(transactions=[])
        assert req.transactions == []


class TestSyncStatusResponse:
    def test_defaults(self):
        resp = SyncStatusResponse(id=1, status="completed")
        assert resp.transactions_found == 0
        assert resp.transactions_imported == 0
        assert resp.transactions_skipped == 0
        assert resp.error_message is None


class TestErrorResponse:
    def test_basic(self):
        resp = ErrorResponse(error="Something failed", errorCode="FAIL")
        assert resp.error == "Something failed"
        assert resp.details is None

    def test_with_details(self):
        resp = ErrorResponse(
            error="Validation failed",
            errorCode="VALIDATION_ERROR",
            details={"field": "name"},
        )
        assert resp.details["field"] == "name"


class TestMonobankAccount:
    def test_minimal(self):
        acc = MonobankAccount(id="acc1", balance=10000, currencyCode=980)
        assert acc.id == "acc1"
        assert acc.creditLimit == 0

    def test_with_optional_fields(self):
        acc = MonobankAccount(
            id="acc1",
            balance=10000,
            currencyCode=980,
            maskedPan=["*1234"],
            iban="UA123",
            type="black",
        )
        assert acc.maskedPan == ["*1234"]


class TestMonobankClientInfo:
    def test_minimal(self):
        info = MonobankClientInfo()
        assert info.accounts == []

    def test_with_accounts(self):
        info = MonobankClientInfo(
            name="Test",
            clientId="cid",
            accounts=[
                MonobankAccount(id="a1", balance=0, currencyCode=980),
            ],
        )
        assert len(info.accounts) == 1


class TestMonobankStatementItem:
    def test_all_required_fields(self):
        item = MonobankStatementItem(
            id="tx1",
            time=1700000000,
            description="Payment",
            mcc=5411,
            amount=-5000,
            operationAmount=-5000,
            currencyCode=980,
            balance=95000,
        )
        assert item.hold is False
        assert item.commissionRate == 0
        assert item.cashbackAmount == 0

    def test_with_optional_fields(self):
        item = MonobankStatementItem(
            id="tx1",
            time=1700000000,
            description="Payment",
            mcc=5411,
            amount=-5000,
            operationAmount=-5000,
            currencyCode=980,
            balance=95000,
            comment="Test comment",
            hold=True,
            receiptId="r123",
        )
        assert item.comment == "Test comment"
        assert item.hold is True
