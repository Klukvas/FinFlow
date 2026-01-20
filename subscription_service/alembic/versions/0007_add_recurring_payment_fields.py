"""Add recurring payment fields

Revision ID: 0007_add_recurring_fields
Revises: 0006_standardize_plans
Create Date: 2026-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0007_add_recurring_fields'
down_revision = '0006_standardize_plans'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add recurring payment fields to subscriptions table
    op.add_column('subscriptions', sa.Column('recurring_token', sa.String(length=255), nullable=True))
    op.add_column('subscriptions', sa.Column('payment_provider', sa.String(length=32), nullable=True))
    op.add_column('subscriptions', sa.Column('last_payment_id', sa.String(length=128), nullable=True))
    op.add_column('subscriptions', sa.Column('next_billing_date', sa.DateTime(), nullable=True))
    op.add_column('subscriptions', sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default='true'))
    
    # Add index for efficient queries
    op.create_index('idx_subscriptions_next_billing', 'subscriptions', ['next_billing_date', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_subscriptions_next_billing', table_name='subscriptions')
    op.drop_column('subscriptions', 'auto_renew')
    op.drop_column('subscriptions', 'next_billing_date')
    op.drop_column('subscriptions', 'last_payment_id')
    op.drop_column('subscriptions', 'payment_provider')
    op.drop_column('subscriptions', 'recurring_token')
