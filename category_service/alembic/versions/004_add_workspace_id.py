"""add workspace_id to categories

Revision ID: 004
Revises: c68a4d210c35
Create Date: 2025-12-20 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = 'c68a4d210c35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add workspace_id column to categories table.
    
    Note: This migration adds the column as nullable first.
    A separate data migration should populate workspace_id from users' personal workspaces.
    After data migration, run another migration to make workspace_id NOT NULL.
    """
    # Add workspace_id column (nullable for now)
    op.add_column(
        'categories',
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Create indexes for workspace queries
    op.create_index(
        'idx_categories_workspace_id',
        'categories',
        ['workspace_id'],
        unique=False
    )
    
    op.create_index(
        'idx_categories_workspace_user',
        'categories',
        ['workspace_id', 'user_id'],
        unique=False
    )
    
    op.create_index(
        'idx_categories_workspace_name_type',
        'categories',
        ['workspace_id', 'name', 'type'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('idx_categories_workspace_name_type', table_name='categories')
    op.drop_index('idx_categories_workspace_user', table_name='categories')
    op.drop_index('idx_categories_workspace_id', table_name='categories')
    
    # Drop column
    op.drop_column('categories', 'workspace_id')


