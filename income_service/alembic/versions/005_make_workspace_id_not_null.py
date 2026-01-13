"""make workspace_id not null

Revision ID: 005
Revises: 004
Create Date: 2025-12-23 14:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make workspace_id NOT NULL after backfill"""
    # First, check if there are any NULL values
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT COUNT(*) FROM incomes WHERE workspace_id IS NULL"))
    null_count = result.scalar()
    
    if null_count > 0:
        print(f"WARNING: Found {null_count} incomes with NULL workspace_id!")
        print("Please run the backfill migration (004) first, or manually assign workspace_id values.")
        raise Exception(f"Cannot set NOT NULL constraint: {null_count} incomes have NULL workspace_id")
    
    # Set NOT NULL constraint
    op.alter_column('incomes', 'workspace_id', nullable=False)


def downgrade() -> None:
    """Remove NOT NULL constraint"""
    op.alter_column('incomes', 'workspace_id', nullable=True)


