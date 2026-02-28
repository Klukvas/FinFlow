"""Change external_transaction_id unique to composite (connection_id, external_transaction_id)

Revision ID: 002
Revises: 001
Create Date: 2026-02-28

"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old global unique constraint
    op.drop_constraint(
        "synced_transactions_external_transaction_id_key",
        "synced_transactions",
        type_="unique",
    )
    # Create composite unique constraint scoped per connection
    op.create_unique_constraint(
        "uq_synced_tx_connection_external",
        "synced_transactions",
        ["connection_id", "external_transaction_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_synced_tx_connection_external",
        "synced_transactions",
        type_="unique",
    )
    op.create_unique_constraint(
        "synced_transactions_external_transaction_id_key",
        "synced_transactions",
        ["external_transaction_id"],
    )
