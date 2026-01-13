"""add default_workspace_id to users

Revision ID: 003
Revises: f02387ac00f2
Create Date: 2025-12-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = 'f02387ac00f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add default_workspace_id column to users table
    op.add_column(
        'users',
        sa.Column('default_workspace_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    # Create index on default_workspace_id for faster lookups
    op.create_index(
        'ix_users_default_workspace_id',
        'users',
        ['default_workspace_id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index first
    op.drop_index('ix_users_default_workspace_id', table_name='users')
    # Drop column
    op.drop_column('users', 'default_workspace_id')

