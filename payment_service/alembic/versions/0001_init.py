"""Initial migration - create payments tables

Revision ID: 0001
Revises: 
Create Date: 2026-01-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('provider', sa.String(64), nullable=False),
        sa.Column('order_reference', sa.String(255), nullable=False, unique=True),
        sa.Column('user_id', sa.String(128), nullable=False),
        sa.Column('workspace_id', sa.String(128), nullable=True),
        sa.Column('purpose', sa.String(64), nullable=False),
        sa.Column('plan_code', sa.String(64), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='UAH'),
        sa.Column('status', sa.String(64), nullable=False, server_default='CREATED'),
        sa.Column('provider_payment_url', sa.Text, nullable=True),
        sa.Column('provider_payload', JSONB, nullable=True),
        sa.Column('provider_response', JSONB, nullable=True),
        sa.Column('paid_at', sa.DateTime, nullable=True),
        sa.Column('failed_at', sa.DateTime, nullable=True),
        sa.Column('refunded_at', sa.DateTime, nullable=True),
        sa.Column('failure_reason', sa.Text, nullable=True),
        sa.Column('extra_data', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('CREATED', 'PENDING', 'PAID', 'FAILED', 'EXPIRED', 'REFUNDED', 'PARTIALLY_REFUNDED', 'CANCELED')",
            name='ck_payment_status',
        ),
        sa.CheckConstraint(
            "provider IN ('WAYFORPAY')",
            name='ck_payment_provider',
        ),
        sa.CheckConstraint(
            "purpose IN ('SUBSCRIPTION', 'ONE_TIME')",
            name='ck_payment_purpose',
        ),
    )

    # Create indexes for payments
    op.create_index('idx_payments_user_created', 'payments', ['user_id', 'created_at'])
    op.create_index('idx_payments_workspace_created', 'payments', ['workspace_id', 'created_at'])
    op.create_index('idx_payments_status_created', 'payments', ['status', 'created_at'])

    # Create payment_events table
    op.create_table(
        'payment_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('payment_id', UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('provider_event_id', sa.String(255), nullable=True),
        sa.Column('signature_valid', sa.Boolean, nullable=True),
        sa.Column('payload_raw', JSONB, nullable=False),
        sa.Column('status_before', sa.String(64), nullable=True),
        sa.Column('status_after', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='CASCADE'),
    )

    # Create indexes for payment_events
    op.create_index('idx_payment_events_payment_created', 'payment_events', ['payment_id', 'created_at'])
    op.create_index('idx_payment_events_provider_event', 'payment_events', ['provider_event_id'])

    # Create idempotency_keys table
    op.create_table(
        'idempotency_keys',
        sa.Column('key', sa.String(255), primary_key=True),
        sa.Column('scope', sa.String(64), nullable=False),
        sa.Column('request_hash', sa.String(64), nullable=False),
        sa.Column('response_body', JSONB, nullable=True),
        sa.Column('response_status', sa.String(16), nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Create index for idempotency_keys
    op.create_index('idx_idempotency_expires', 'idempotency_keys', ['expires_at'])


def downgrade() -> None:
    op.drop_table('idempotency_keys')
    op.drop_table('payment_events')
    op.drop_table('payments')
