"""add index on synced_transactions.connection_id

Revision ID: 004
Revises: 003
"""
from alembic import op

revision = "004"
down_revision = "003"


def upgrade() -> None:
    op.create_index(
        "ix_synced_transactions_connection_id",
        "synced_transactions",
        ["connection_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_synced_transactions_connection_id", table_name="synced_transactions"
    )
