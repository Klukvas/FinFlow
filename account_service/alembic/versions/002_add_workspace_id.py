"""add workspace_id to accounts

Revision ID: 002
Revises: 001
Create Date: 2025-12-23 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add workspace_id column to accounts table.
    
    Note: This migration adds the column as nullable first.
    A separate data migration should populate workspace_id from users' personal workspaces.
    After data migration, run another migration to make workspace_id NOT NULL.
    """
    # Add workspace_id column (nullable for now)
    op.add_column(
        'accounts',
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Create indexes for workspace queries
    op.create_index(
        'idx_accounts_workspace_id',
        'accounts',
        ['workspace_id'],
        unique=False
    )
    
    op.create_index(
        'idx_accounts_workspace_owner',
        'accounts',
        ['workspace_id', 'owner_id'],
        unique=False
    )
    
    op.create_index(
        'idx_accounts_workspace_name',
        'accounts',
        ['workspace_id', 'name'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('idx_accounts_workspace_name', table_name='accounts')
    op.drop_index('idx_accounts_workspace_owner', table_name='accounts')
    op.drop_index('idx_accounts_workspace_id', table_name='accounts')
    
    # Drop column
    op.drop_column('accounts', 'workspace_id')


