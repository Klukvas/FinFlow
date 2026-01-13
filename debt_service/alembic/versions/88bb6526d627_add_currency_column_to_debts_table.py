"""add currency column to debts table

Revision ID: 88bb6526d627
Revises: 8dfb3b1b990d
Create Date: 2025-10-27 16:00:03.897283

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88bb6526d627'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add currency column to debts table
    op.add_column('debts', sa.Column('currency', sa.String(3), nullable=False, server_default='USD'))


def downgrade() -> None:
    # Remove currency column from debts table
    op.drop_column('debts', 'currency')
