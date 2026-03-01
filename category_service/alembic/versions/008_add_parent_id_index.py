"""add index on parent_id

Revision ID: 008
Revises: 007
"""
from alembic import op

revision = "008"
down_revision = "007"


def upgrade() -> None:
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_categories_parent_id", table_name="categories")
