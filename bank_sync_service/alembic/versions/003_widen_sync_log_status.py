"""Widen sync_logs.status from varchar(20) to varchar(30)

Revision ID: 003
Revises: 002
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "sync_logs",
        "status",
        type_=sa.String(30),
        existing_type=sa.String(20),
    )


def downgrade() -> None:
    op.alter_column(
        "sync_logs",
        "status",
        type_=sa.String(20),
        existing_type=sa.String(30),
    )
