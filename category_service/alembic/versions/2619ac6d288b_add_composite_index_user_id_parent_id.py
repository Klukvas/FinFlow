"""add_composite_index_user_id_parent_id

Revision ID: 2619ac6d288b
Revises: b61576c61737
Create Date: 2025-10-16 19:50:01.890385

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2619ac6d288b'
down_revision: Union[str, None] = 'b61576c61737'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create composite index for efficient filtering by user_id and parent_id
    op.create_index(
        'ix_categories_user_id_parent_id', 
        'categories', 
        ['user_id', 'parent_id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the composite index
    op.drop_index('ix_categories_user_id_parent_id', table_name='categories')
