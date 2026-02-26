"""Convert float columns to numeric for monetary precision

Revision ID: 0006_float_to_numeric
Revises: 0005_make_workspace_id_not_null
Create Date: 2026-02-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0006_float_to_numeric'
down_revision = '0005_make_workspace_id_not_null'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Goal table — monetary columns
    op.execute("ALTER TABLE goals ALTER COLUMN target_amount TYPE NUMERIC(12,2) USING target_amount::numeric(12,2)")
    op.execute("ALTER TABLE goals ALTER COLUMN current_amount TYPE NUMERIC(12,2) USING current_amount::numeric(12,2)")
    # Progress percentage needs higher precision
    op.execute("ALTER TABLE goals ALTER COLUMN progress_percentage TYPE NUMERIC(8,4) USING progress_percentage::numeric(8,4)")

    # Milestone table — monetary columns
    op.execute("ALTER TABLE milestones ALTER COLUMN target_amount TYPE NUMERIC(12,2) USING target_amount::numeric(12,2)")
    op.execute("ALTER TABLE milestones ALTER COLUMN current_amount TYPE NUMERIC(12,2) USING current_amount::numeric(12,2)")


def downgrade() -> None:
    op.execute("ALTER TABLE goals ALTER COLUMN target_amount TYPE DOUBLE PRECISION USING target_amount::double precision")
    op.execute("ALTER TABLE goals ALTER COLUMN current_amount TYPE DOUBLE PRECISION USING current_amount::double precision")
    op.execute("ALTER TABLE goals ALTER COLUMN progress_percentage TYPE DOUBLE PRECISION USING progress_percentage::double precision")

    op.execute("ALTER TABLE milestones ALTER COLUMN target_amount TYPE DOUBLE PRECISION USING target_amount::double precision")
    op.execute("ALTER TABLE milestones ALTER COLUMN current_amount TYPE DOUBLE PRECISION USING current_amount::double precision")
