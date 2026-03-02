"""add index on categories.mcc_code

Revision ID: 009
Revises: 008
"""
from alembic import op

revision = "009"
down_revision = "008"


def upgrade() -> None:
    op.create_index("ix_categories_mcc_code", "categories", ["mcc_code"])


def downgrade() -> None:
    op.drop_index("ix_categories_mcc_code", table_name="categories")
