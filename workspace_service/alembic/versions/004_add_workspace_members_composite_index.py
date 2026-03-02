"""add composite index on workspace_members (workspace_id, status)

Revision ID: 004
Revises: 003
"""
from alembic import op

revision = "004"
down_revision = "003"


def upgrade() -> None:
    op.create_index(
        "idx_workspace_members_ws_status",
        "workspace_members",
        ["workspace_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("idx_workspace_members_ws_status", table_name="workspace_members")
