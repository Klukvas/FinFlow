"""add index on milestones.goal_id

Revision ID: 0007
Revises: 0006
"""
from alembic import op

revision = "0007"
down_revision = "0006"


def upgrade() -> None:
    op.create_index("ix_milestones_goal_id", "milestones", ["goal_id"])
    op.create_index(
        "idx_milestones_goal_order", "milestones", ["goal_id", "order_index"]
    )


def downgrade() -> None:
    op.drop_index("idx_milestones_goal_order", table_name="milestones")
    op.drop_index("ix_milestones_goal_id", table_name="milestones")
