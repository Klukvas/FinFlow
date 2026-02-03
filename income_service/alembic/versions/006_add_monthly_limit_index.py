"""add index for monthly limit checks

Revision ID: 006
Revises: 005
Create Date: 2026-01-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add index on (user_id, created_at) for monthly limit counting performance"""
    op.create_index(
        'idx_incomes_user_created',
        'incomes',
        ['user_id', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    """Remove index on (user_id, created_at)"""
    op.drop_index('idx_incomes_user_created', table_name='incomes')
