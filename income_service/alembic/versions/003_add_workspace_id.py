"""add workspace_id to incomes

Revision ID: 003
Revises: 002
Create Date: 2025-12-23 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002_add_currency_to_incomes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add workspace_id column to incomes table.
    
    Note: This migration adds the column as nullable first.
    A separate data migration should populate workspace_id from users' personal workspaces.
    After data migration, run another migration to make workspace_id NOT NULL.
    """
    # Add workspace_id column (nullable for now)
    op.add_column(
        'incomes',
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Create indexes for workspace queries
    op.create_index(
        'idx_incomes_workspace_id',
        'incomes',
        ['workspace_id'],
        unique=False
    )
    
    op.create_index(
        'idx_incomes_workspace_user',
        'incomes',
        ['workspace_id', 'user_id'],
        unique=False
    )
    
    op.create_index(
        'idx_incomes_workspace_date',
        'incomes',
        ['workspace_id', 'date'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('idx_incomes_workspace_date', table_name='incomes')
    op.drop_index('idx_incomes_workspace_user', table_name='incomes')
    op.drop_index('idx_incomes_workspace_id', table_name='incomes')
    
    # Drop column
    op.drop_column('incomes', 'workspace_id')


