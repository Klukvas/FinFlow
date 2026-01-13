"""make workspace_id not null

Revision ID: 004
Revises: 003
Create Date: 2025-12-23 22:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make workspace_id NOT NULL after backfill"""
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT COUNT(*) FROM recurring_payments WHERE workspace_id IS NULL"))
    null_count = result.scalar()
    
    if null_count > 0:
        raise Exception(f"Cannot set NOT NULL: {null_count} recurring_payments have NULL workspace_id")
    
    # Set NOT NULL constraint
    op.alter_column('recurring_payments', 'workspace_id', nullable=False)


def downgrade() -> None:
    """Remove NOT NULL constraint"""
    op.alter_column('recurring_payments', 'workspace_id', nullable=True)


