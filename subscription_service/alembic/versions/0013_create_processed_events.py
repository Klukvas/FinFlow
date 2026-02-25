"""Create processed_internal_events table for Paddle event idempotency

Revision ID: 0013_processed_events
Revises: 0012_add_price_to_plans
Create Date: 2026-02-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0013_processed_events'
down_revision = '0012_add_price_to_plans'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'processed_internal_events',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('event_key', sa.String(255), unique=True, nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_processed_internal_events_key', 'processed_internal_events', ['event_key'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_processed_internal_events_key')
    op.drop_table('processed_internal_events')
