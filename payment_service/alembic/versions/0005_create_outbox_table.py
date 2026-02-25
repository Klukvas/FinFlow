"""Create outbox_events table for reliable cross-service notifications

Revision ID: 0005_create_outbox
Revises: 0004_add_price_validation
Create Date: 2026-02-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '0005_create_outbox'
down_revision = '0004_add_price_validation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'outbox_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('aggregate_type', sa.String(64), nullable=False),
        sa.Column('aggregate_id', UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('payload', JSONB, nullable=False),
        sa.Column('destination_url', sa.String(512), nullable=False),
        sa.Column('headers', JSONB, nullable=True),
        sa.Column('status', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('next_retry_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'processing', 'delivered', 'failed')", name='ck_outbox_status'),
    )
    op.create_index('idx_outbox_pending', 'outbox_events', ['status', 'next_retry_at'])
    op.create_index('idx_outbox_aggregate', 'outbox_events', ['aggregate_type', 'aggregate_id'])


def downgrade() -> None:
    op.drop_index('idx_outbox_aggregate')
    op.drop_index('idx_outbox_pending')
    op.drop_table('outbox_events')
