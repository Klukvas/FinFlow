"""
Tests for app/models/account.py — SQLAlchemy model and AccountType enum.
"""
import pytest
from datetime import datetime
from uuid import UUID

from app.models.account import Account, AccountType
from app.tests.conftest import TestingSessionLocal, TEST_WORKSPACE_ID


class TestAccountType:
    def test_all_types_exist(self):
        expected = ["cash", "bank", "crypto", "investment", "credit", "savings", "checking"]
        actual = [t.value for t in AccountType]
        for t in expected:
            assert t in actual

    def test_is_string_enum(self):
        assert isinstance(AccountType.CASH, str)
        assert AccountType.CASH == "cash"

    def test_count(self):
        assert len(AccountType) == 7


class TestAccountModel:
    def test_create_and_retrieve(self):
        db = TestingSessionLocal()
        try:
            account = Account(
                name="Test",
                type=AccountType.SAVINGS,
                currency="USD",
                balance=100.0,
                owner_id=1,
                workspace_id=TEST_WORKSPACE_ID,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(account)
            db.commit()
            db.refresh(account)

            fetched = db.query(Account).filter(Account.id == account.id).first()
            assert fetched is not None
            assert fetched.name == "Test"
            assert fetched.type == AccountType.SAVINGS
            assert fetched.currency == "USD"
            assert float(fetched.balance) == 100.0
            assert fetched.owner_id == 1
            assert fetched.is_active is True
            assert fetched.is_archived is False
        finally:
            db.query(Account).delete()
            db.commit()
            db.close()

    def test_defaults(self):
        db = TestingSessionLocal()
        try:
            account = Account(
                name="Defaults",
                type=AccountType.CASH,
                currency="EUR",
                owner_id=2,
                workspace_id=TEST_WORKSPACE_ID,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(account)
            db.commit()
            db.refresh(account)

            assert account.is_active is True
            assert account.is_archived is False
            assert account.description is None
        finally:
            db.query(Account).delete()
            db.commit()
            db.close()

    def test_repr(self):
        account = Account(
            id=1,
            name="Repr Test",
            type=AccountType.BANK,
            balance=500.0,
        )
        repr_str = repr(account)
        assert "Account" in repr_str
        assert "Repr Test" in repr_str
        assert "1" in repr_str

    def test_nullable_description(self):
        db = TestingSessionLocal()
        try:
            account = Account(
                name="No Desc",
                type=AccountType.CASH,
                currency="USD",
                owner_id=1,
                workspace_id=TEST_WORKSPACE_ID,
                description=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            assert account.description is None
        finally:
            db.query(Account).delete()
            db.commit()
            db.close()

    def test_with_description(self):
        db = TestingSessionLocal()
        try:
            account = Account(
                name="With Desc",
                type=AccountType.SAVINGS,
                currency="USD",
                owner_id=1,
                workspace_id=TEST_WORKSPACE_ID,
                description="My savings account",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            assert account.description == "My savings account"
        finally:
            db.query(Account).delete()
            db.commit()
            db.close()
