"""add_composite_index_user_id_name

Revision ID: 1cd77d51bce1
Revises: 2619ac6d288b
Create Date: 2025-10-16 19:55:44.130478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1cd77d51bce1'
down_revision: Union[str, None] = '2619ac6d288b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create composite index for efficient name uniqueness validation
    # This speeds up the query: WHERE user_id = X AND name = Y
    op.create_index(
        'ix_categories_user_id_name', 
        'categories', 
        ['user_id', 'name']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the composite index
    op.drop_index('ix_categories_user_id_name', table_name='categories')
