"""add timestamp columns and index for monthly limit checks

Revision ID: 010
Revises: 009
Create Date: 2026-01-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '2adb54e9430e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add created_at and updated_at columns, then add index for monthly limit counting"""
    # Add timestamp columns
    op.add_column('expenses', sa.Column('created_at', sa.DateTime(), server_default=func.now(), nullable=False))
    op.add_column('expenses', sa.Column('updated_at', sa.DateTime(), server_default=func.now(), nullable=False))

    # Add index on (user_id, created_at) for monthly limit counting performance
    op.create_index(
        'idx_expenses_user_created',
        'expenses',
        ['user_id', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    """Remove index and timestamp columns"""
    op.drop_index('idx_expenses_user_created', table_name='expenses')
    op.drop_column('expenses', 'updated_at')
    op.drop_column('expenses', 'created_at')
