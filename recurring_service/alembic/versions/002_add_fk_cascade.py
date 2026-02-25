"""Add CASCADE on delete to payment_schedules FK

Revision ID: 002
Revises: 001
Create Date: 2026-02-25 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

FK_NAME = 'payment_schedules_recurring_payment_id_fkey'


def upgrade() -> None:
    op.drop_constraint(FK_NAME, 'payment_schedules', type_='foreignkey')
    op.create_foreign_key(
        FK_NAME,
        'payment_schedules',
        'recurring_payments',
        ['recurring_payment_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint(FK_NAME, 'payment_schedules', type_='foreignkey')
    op.create_foreign_key(
        FK_NAME,
        'payment_schedules',
        'recurring_payments',
        ['recurring_payment_id'],
        ['id'],
    )
