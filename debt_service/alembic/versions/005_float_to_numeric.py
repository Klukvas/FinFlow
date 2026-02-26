"""Convert float columns to numeric for monetary precision

Revision ID: 005_float_to_numeric
Revises: 88bb6526d627
Create Date: 2026-02-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_float_to_numeric'
down_revision = '88bb6526d627'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Debt table — monetary columns
    op.execute("ALTER TABLE debts ALTER COLUMN initial_amount TYPE NUMERIC(12,2) USING initial_amount::numeric(12,2)")
    op.execute("ALTER TABLE debts ALTER COLUMN current_balance TYPE NUMERIC(12,2) USING current_balance::numeric(12,2)")
    op.execute("ALTER TABLE debts ALTER COLUMN minimum_payment TYPE NUMERIC(12,2) USING minimum_payment::numeric(12,2)")
    # Interest rate needs higher precision
    op.execute("ALTER TABLE debts ALTER COLUMN interest_rate TYPE NUMERIC(8,4) USING interest_rate::numeric(8,4)")

    # DebtPayment table — monetary columns
    op.execute("ALTER TABLE debt_payments ALTER COLUMN amount TYPE NUMERIC(12,2) USING amount::numeric(12,2)")
    op.execute("ALTER TABLE debt_payments ALTER COLUMN principal_amount TYPE NUMERIC(12,2) USING principal_amount::numeric(12,2)")
    op.execute("ALTER TABLE debt_payments ALTER COLUMN interest_amount TYPE NUMERIC(12,2) USING interest_amount::numeric(12,2)")


def downgrade() -> None:
    op.execute("ALTER TABLE debts ALTER COLUMN initial_amount TYPE DOUBLE PRECISION USING initial_amount::double precision")
    op.execute("ALTER TABLE debts ALTER COLUMN current_balance TYPE DOUBLE PRECISION USING current_balance::double precision")
    op.execute("ALTER TABLE debts ALTER COLUMN minimum_payment TYPE DOUBLE PRECISION USING minimum_payment::double precision")
    op.execute("ALTER TABLE debts ALTER COLUMN interest_rate TYPE DOUBLE PRECISION USING interest_rate::double precision")

    op.execute("ALTER TABLE debt_payments ALTER COLUMN amount TYPE DOUBLE PRECISION USING amount::double precision")
    op.execute("ALTER TABLE debt_payments ALTER COLUMN principal_amount TYPE DOUBLE PRECISION USING principal_amount::double precision")
    op.execute("ALTER TABLE debt_payments ALTER COLUMN interest_amount TYPE DOUBLE PRECISION USING interest_amount::double precision")
