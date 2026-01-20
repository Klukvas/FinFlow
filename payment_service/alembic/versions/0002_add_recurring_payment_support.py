"""Add recurring payment support

Revision ID: 0002_recurring_support
Revises: 0001
Create Date: 2026-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_recurring_support'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add recurring payment fields to payments table
    op.add_column('payments', sa.Column('recurring_token', sa.String(length=255), nullable=True))
    op.add_column('payments', sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add index for recurring token lookups
    op.create_index('idx_payments_recurring_token', 'payments', ['recurring_token'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_payments_recurring_token', table_name='payments')
    op.drop_column('payments', 'is_recurring')
    op.drop_column('payments', 'recurring_token')
