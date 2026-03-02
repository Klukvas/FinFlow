"""add indexes on debt.contact_id and debt_payments.debt_id

Revision ID: 006
Revises: 005
"""
from alembic import op

revision = "006"
down_revision = "005_float_to_numeric"


def upgrade() -> None:
    op.create_index("ix_debts_contact_id", "debts", ["contact_id"])
    op.create_index("ix_debt_payments_debt_id", "debt_payments", ["debt_id"])
    op.create_index(
        "idx_debt_payments_user_debt", "debt_payments", ["user_id", "debt_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_debt_payments_user_debt", table_name="debt_payments")
    op.drop_index("ix_debt_payments_debt_id", table_name="debt_payments")
    op.drop_index("ix_debts_contact_id", table_name="debts")
