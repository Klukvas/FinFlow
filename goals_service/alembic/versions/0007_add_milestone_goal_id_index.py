"""add composite index on milestones (goal_id, order_index)

Revision ID: 0007
Revises: 0006_float_to_numeric
"""
from alembic import op

revision = "0007"
down_revision = "0006_float_to_numeric"


def upgrade() -> None:
    # ix_milestones_goal_id already exists from 0001_initial — skip it
    op.create_index(
        "idx_milestones_goal_order", "milestones", ["goal_id", "order_index"]
    )


def downgrade() -> None:
    op.drop_index("idx_milestones_goal_order", table_name="milestones")
