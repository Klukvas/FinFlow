"""add_category_fields_for_mcc

Revision ID: add_category_fields_for_mcc
Revises: create_mcc
Create Date: 2025-10-26 19:50:01.890385

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_category_fields_for_mcc'
down_revision: Union[str, None] = 'create_mcc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Create enum for created_by
category_created_by_enum = sa.Enum('USER', 'SYSTEM', name='categorycreatedby')


def upgrade() -> None:
    """Add fields to categories for MCC integration."""
    # Create enum type
    category_created_by_enum.create(op.get_bind())
    
    # Add column created_by
    op.add_column(
        'categories',
        sa.Column('created_by', category_created_by_enum, nullable=True, server_default='USER')
    )
    
    # Add columns for MCC relationship
    op.add_column('categories', sa.Column('mcc_code', sa.Integer(), nullable=True))
    op.add_column('categories', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()))
    op.add_column('categories', sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()))
    
    # Create foreign key on mcc_codes
    op.create_foreign_key(
        'fk_categories_mcc_code',
        'categories',
        'mcc_codes',
        ['mcc_code'],
        ['mcc_code'],
        ondelete='SET NULL'
    )
    
    # Update existing rows
    op.execute("UPDATE categories SET created_by = 'USER' WHERE created_by IS NULL")
    
    # Make column NOT NULL after filling
    op.alter_column('categories', 'created_by', nullable=False, server_default='USER')


    # Make column NOT NULL after filling
    op.execute("UPDATE categories SET created_at = NOW() WHERE created_at IS NULL")
    op.alter_column('categories', 'created_at', nullable=False)



def downgrade() -> None:
    """Remove fields from categories."""
    # Remove foreign key
    op.drop_constraint('fk_categories_mcc_code', 'categories', type_='foreignkey')
    
    # Remove columns
    op.drop_column('categories', 'updated_at')
    op.drop_column('categories', 'created_at')
    op.drop_column('categories', 'mcc_code')
    op.drop_column('categories', 'created_by')
    
    # Remove enum type
    category_created_by_enum.drop(op.get_bind())