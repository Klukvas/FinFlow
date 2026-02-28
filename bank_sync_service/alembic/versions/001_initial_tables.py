"""Initial bank sync tables

Revision ID: 001
Revises:
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bank_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", UUID(as_uuid=True), nullable=False),
        sa.Column("bank_type", sa.String(50), server_default="monobank"),
        sa.Column("encrypted_token", sa.Text(), nullable=False),
        sa.Column("client_name", sa.String(200), nullable=True),
        sa.Column("client_id", sa.String(100), nullable=True),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_bank_connections_user_id", "bank_connections", ["user_id"])
    op.create_index("ix_bank_connections_workspace_id", "bank_connections", ["workspace_id"])
    op.create_index("ix_bank_connections_workspace_user", "bank_connections", ["workspace_id", "user_id"])

    op.create_table(
        "linked_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("connection_id", sa.Integer(), sa.ForeignKey("bank_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_account_id", sa.String(100), nullable=False),
        sa.Column("finflow_account_id", sa.Integer(), nullable=True),
        sa.Column("account_name", sa.String(200)),
        sa.Column("currency_code", sa.Integer()),
        sa.Column("currency", sa.String(3)),
        sa.Column("masked_pan", sa.String(100), nullable=True),
        sa.Column("iban", sa.String(50), nullable=True),
        sa.Column("is_synced", sa.Boolean(), server_default="true"),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "sync_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("connection_id", sa.Integer(), sa.ForeignKey("bank_connections.id", ondelete="CASCADE")),
        sa.Column("linked_account_id", sa.Integer(), sa.ForeignKey("linked_accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("transactions_found", sa.Integer(), server_default="0"),
        sa.Column("transactions_imported", sa.Integer(), server_default="0"),
        sa.Column("transactions_skipped", sa.Integer(), server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sync_from", sa.DateTime(), nullable=True),
        sa.Column("sync_to", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "synced_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("connection_id", sa.Integer(), sa.ForeignKey("bank_connections.id", ondelete="CASCADE")),
        sa.Column("external_transaction_id", sa.String(100), nullable=False, unique=True),
        sa.Column("finflow_type", sa.String(10)),
        sa.Column("finflow_id", sa.Integer()),
        sa.Column("amount", sa.Numeric(12, 2)),
        sa.Column("date", sa.Date()),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_synced_transactions_external_id", "synced_transactions", ["external_transaction_id"])


def downgrade() -> None:
    op.drop_table("synced_transactions")
    op.drop_table("sync_logs")
    op.drop_table("linked_accounts")
    op.drop_table("bank_connections")
