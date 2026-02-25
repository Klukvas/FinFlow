"""Add partial unique index on outbox_events for reconciliation dedup

Prevents duplicate re-enqueue when reconciliation detects the same mismatch
concurrently. The index covers (aggregate_id, event_type) for rows with
status IN ('pending', 'processing').

Revision ID: 0007_outbox_dedup
Revises: 0006_admin_audit
Create Date: 2026-02-25 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '0007_outbox_dedup'
down_revision = '0006_admin_audit'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_outbox_pending_aggregate_event",
        "outbox_events",
        ["aggregate_id", "event_type"],
        unique=True,
        postgresql_where="status IN ('pending', 'processing')",
    )


def downgrade() -> None:
    op.drop_index("uq_outbox_pending_aggregate_event", table_name="outbox_events")
