"""add workspace_id to expenses

Revision ID: 007
Revises: c8ce19e9fd1b
Create Date: 2025-12-23 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = 'c8ce19e9fd1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add workspace_id column to expenses table.
    
    Note: This migration adds the column as nullable first.
    A separate data migration should populate workspace_id from users' personal workspaces.
    After data migration, run another migration to make workspace_id NOT NULL.
    """
    # Add workspace_id column (nullable for now)
    op.add_column(
        'expenses',
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Create indexes for workspace queries
    op.create_index(
        'idx_expenses_workspace_id',
        'expenses',
        ['workspace_id'],
        unique=False
    )
    
    op.create_index(
        'idx_expenses_workspace_user',
        'expenses',
        ['workspace_id', 'user_id'],
        unique=False
    )
    
    op.create_index(
        'idx_expenses_workspace_date',
        'expenses',
        ['workspace_id', 'date'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('idx_expenses_workspace_date', table_name='expenses')
    op.drop_index('idx_expenses_workspace_user', table_name='expenses')
    op.drop_index('idx_expenses_workspace_id', table_name='expenses')
    
    # Drop column
    op.drop_column('expenses', 'workspace_id')



