"""add_type_to_categories

Revision ID: b61576c61737
Revises: c6d7e35a6e52
Create Date: 2025-09-23 23:40:50.894009

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b61576c61737'
down_revision: Union[str, None] = 'c6d7e35a6e52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the enum type first
    categorytype_enum = sa.Enum('EXPENSE', 'INCOME', name='categorytype')
    categorytype_enum.create(op.get_bind())
    
    # Add the column with the enum type and default value
    op.add_column('categories', sa.Column('type', categorytype_enum, nullable=True, server_default='EXPENSE'))
    
    # Update existing rows to have the default value
    op.execute("UPDATE categories SET type = 'EXPENSE' WHERE type IS NULL")
    
    # Finally make the column NOT NULL
    op.alter_column('categories', 'type', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the column first
    op.drop_column('categories', 'type')
    
    # Then drop the enum type
    categorytype_enum = sa.Enum('EXPENSE', 'INCOME', name='categorytype')
    categorytype_enum.drop(op.get_bind())
