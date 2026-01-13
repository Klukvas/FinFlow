"""Make workspace_id not null

Revision ID: 0005_make_workspace_id_not_null
Revises: 0004_backfill_workspace_id
Create Date: 2025-01-27 15:02:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005_make_workspace_id_not_null'
down_revision = '0004_backfill_workspace_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make workspace_id NOT NULL
    op.alter_column('goals', 'workspace_id',
                    existing_type=sa.UUID(),
                    nullable=False)


def downgrade() -> None:
    # Make workspace_id nullable again
    op.alter_column('goals', 'workspace_id',
                    existing_type=sa.UUID(),
                    nullable=True)

