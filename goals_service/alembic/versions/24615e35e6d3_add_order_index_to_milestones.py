"""add_order_index_to_milestones

Revision ID: 24615e35e6d3
Revises: 0001_initial
Create Date: 2025-10-27 20:56:09.983334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24615e35e6d3'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add order_index column to milestones table
    op.add_column('milestones', sa.Column('order_index', sa.Integer(), nullable=True, server_default='0'))
    
    # Set default value for existing records
    op.execute("UPDATE milestones SET order_index = 0 WHERE order_index IS NULL")
    
    # Make the column not nullable now that all rows have values
    op.alter_column('milestones', 'order_index', nullable=False)


def downgrade() -> None:
    # Remove order_index column from milestones table
    op.drop_column('milestones', 'order_index')
