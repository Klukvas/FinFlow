"""Add Paddle Billing support

Revision ID: 0003_add_paddle_support
Revises: 0002_recurring_support
Create Date: 2026-02-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '0003_add_paddle_support'
down_revision = '0002_recurring_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Update provider check constraint to include PADDLE
    op.drop_constraint('ck_payment_provider', 'payments')
    op.create_check_constraint(
        'ck_payment_provider',
        'payments',
        "provider IN ('WAYFORPAY', 'PADDLE')",
    )

    # 2. Add Paddle-specific columns to payments table
    op.add_column(
        'payments',
        sa.Column('paddle_customer_id', sa.String(length=255), nullable=True),
    )
    op.add_column(
        'payments',
        sa.Column('paddle_subscription_id', sa.String(length=255), nullable=True),
    )
    op.add_column(
        'payments',
        sa.Column('paddle_transaction_id', sa.String(length=255), nullable=True),
    )

    # 3. Create processed_webhook_events table for idempotent webhook handling
    op.create_table(
        'processed_webhook_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('event_id', sa.String(length=255), unique=True, nullable=False),
        sa.Column('event_type', sa.String(length=128), nullable=False),
        sa.Column(
            'processed_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
    )

    # 4. Create paddle_price_map table for plan-to-price mapping
    op.create_table(
        'paddle_price_map',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('plan_code', sa.String(length=64), unique=True, nullable=False),
        sa.Column('paddle_price_id', sa.String(length=255), nullable=False),
        sa.Column(
            'billing_period',
            sa.String(length=16),
            nullable=False,
            server_default='monthly',
        ),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # 5. Add indexes on new Paddle columns for efficient lookups
    op.create_index(
        'idx_payments_paddle_customer_id',
        'payments',
        ['paddle_customer_id'],
        unique=False,
    )
    op.create_index(
        'idx_payments_paddle_subscription_id',
        'payments',
        ['paddle_subscription_id'],
        unique=False,
    )
    op.create_index(
        'idx_payments_paddle_transaction_id',
        'payments',
        ['paddle_transaction_id'],
        unique=False,
    )
    op.create_index(
        'idx_processed_webhook_events_event_id',
        'processed_webhook_events',
        ['event_id'],
        unique=True,
    )
    op.create_index(
        'idx_paddle_price_map_plan_code',
        'paddle_price_map',
        ['plan_code'],
        unique=True,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_paddle_price_map_plan_code', table_name='paddle_price_map')
    op.drop_index(
        'idx_processed_webhook_events_event_id',
        table_name='processed_webhook_events',
    )
    op.drop_index('idx_payments_paddle_transaction_id', table_name='payments')
    op.drop_index('idx_payments_paddle_subscription_id', table_name='payments')
    op.drop_index('idx_payments_paddle_customer_id', table_name='payments')

    # Drop new tables
    op.drop_table('paddle_price_map')
    op.drop_table('processed_webhook_events')

    # Remove Paddle columns from payments
    op.drop_column('payments', 'paddle_transaction_id')
    op.drop_column('payments', 'paddle_subscription_id')
    op.drop_column('payments', 'paddle_customer_id')

    # Restore original provider constraint (WAYFORPAY only)
    op.drop_constraint('ck_payment_provider', 'payments')
    op.create_check_constraint(
        'ck_payment_provider',
        'payments',
        "provider IN ('WAYFORPAY')",
    )
