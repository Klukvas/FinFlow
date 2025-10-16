"""add_composite_index_user_id_type

Revision ID: e138e7a86b02
Revises: 1cd77d51bce1
Create Date: 2025-10-16 19:56:11.008995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e138e7a86b02'
down_revision: Union[str, None] = '1cd77d51bce1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create composite index for efficient category type filtering
    # This speeds up queries like: WHERE user_id = X AND type = 'EXPENSE'
    op.create_index(
        'ix_categories_user_id_type', 
        'categories', 
        ['user_id', 'type']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the composite index
    op.drop_index('ix_categories_user_id_type', table_name='categories')
