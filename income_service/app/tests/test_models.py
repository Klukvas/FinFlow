"""Tests for app/models/income.py — SQLAlchemy model structure."""
import pytest
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import inspect

from app.models.income import Income
from app.database import Base


class TestIncomeModel:
    def test_tablename(self):
        assert Income.__tablename__ == "incomes"

    def test_inherits_base(self):
        assert issubclass(Income, Base)

    def test_has_required_columns(self):
        mapper = inspect(Income)
        column_names = {col.key for col in mapper.columns}
        expected = {
            "id",
            "user_id",
            "workspace_id",
            "amount",
            "category_id",
            "account_id",
            "currency",
            "description",
            "date",
            "created_at",
            "updated_at",
        }
        assert expected.issubset(column_names)

    def test_id_is_primary_key(self):
        mapper = inspect(Income)
        pk_cols = [col.key for col in mapper.columns if col.primary_key]
        assert "id" in pk_cols

    def test_user_id_not_nullable(self):
        mapper = inspect(Income)
        user_id_col = mapper.columns["user_id"]
        assert not user_id_col.nullable

    def test_workspace_id_not_nullable(self):
        mapper = inspect(Income)
        ws_col = mapper.columns["workspace_id"]
        assert not ws_col.nullable

    def test_amount_not_nullable(self):
        mapper = inspect(Income)
        amount_col = mapper.columns["amount"]
        assert not amount_col.nullable

    def test_category_id_nullable(self):
        mapper = inspect(Income)
        cat_col = mapper.columns["category_id"]
        assert cat_col.nullable

    def test_account_id_nullable(self):
        mapper = inspect(Income)
        acc_col = mapper.columns["account_id"]
        assert acc_col.nullable

    def test_description_nullable(self):
        mapper = inspect(Income)
        desc_col = mapper.columns["description"]
        assert desc_col.nullable

    def test_currency_not_nullable(self):
        mapper = inspect(Income)
        cur_col = mapper.columns["currency"]
        assert not cur_col.nullable

    def test_create_instance(self):
        ws = uuid4()
        income = Income(
            user_id=1,
            workspace_id=ws,
            amount=100.50,
            currency="USD",
            description="test",
            date=datetime.utcnow(),
        )
        assert income.user_id == 1
        assert income.workspace_id == ws
        assert income.amount == 100.50
        assert income.currency == "USD"

    def test_table_args_has_composite_indexes(self):
        table_args = Income.__table_args__
        index_names = {idx.name for idx in table_args if hasattr(idx, "name")}
        assert "idx_incomes_workspace_user" in index_names
        assert "idx_incomes_workspace_date" in index_names
