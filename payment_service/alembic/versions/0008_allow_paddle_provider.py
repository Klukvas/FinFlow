"""Allow PADDLE provider in payments check constraint

Revision ID: 0008_paddle_provider
Revises: 0007_outbox_dedup
Create Date: 2026-02-25 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '0008_paddle_provider'
down_revision = '0007_outbox_dedup'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint('ck_payment_provider', 'payments', type_='check')
    op.create_check_constraint(
        'ck_payment_provider',
        'payments',
        "provider IN ('WAYFORPAY', 'PADDLE')",
    )


def downgrade() -> None:
    op.drop_constraint('ck_payment_provider', 'payments', type_='check')
    op.create_check_constraint(
        'ck_payment_provider',
        'payments',
        "provider IN ('WAYFORPAY')",
    )
