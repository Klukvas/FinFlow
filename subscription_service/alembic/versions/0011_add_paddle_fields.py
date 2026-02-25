"""Add Paddle Billing fields to subscriptions

Revision ID: 0011_add_paddle_fields
Revises: 0010_add_pdf_features
Create Date: 2026-02-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0011_add_paddle_fields'
down_revision = '0010_add_pdf_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Paddle-specific columns to subscriptions table
    op.add_column(
        'subscriptions',
        sa.Column('paddle_customer_id', sa.String(length=255), nullable=True),
    )
    op.add_column(
        'subscriptions',
        sa.Column('paddle_subscription_id', sa.String(length=255), nullable=True),
    )
    op.add_column(
        'subscriptions',
        sa.Column('paddle_price_id', sa.String(length=255), nullable=True),
    )

    # Add indexes for efficient Paddle-related lookups
    op.create_index(
        'idx_subscriptions_paddle_customer_id',
        'subscriptions',
        ['paddle_customer_id'],
        unique=False,
    )
    op.create_index(
        'idx_subscriptions_paddle_subscription_id',
        'subscriptions',
        ['paddle_subscription_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        'idx_subscriptions_paddle_subscription_id',
        table_name='subscriptions',
    )
    op.drop_index(
        'idx_subscriptions_paddle_customer_id',
        table_name='subscriptions',
    )
    op.drop_column('subscriptions', 'paddle_price_id')
    op.drop_column('subscriptions', 'paddle_subscription_id')
    op.drop_column('subscriptions', 'paddle_customer_id')
