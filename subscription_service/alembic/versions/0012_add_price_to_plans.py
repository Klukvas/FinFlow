"""Add price and currency columns to plans table

Revision ID: 0012_add_price_to_plans
Revises: 0011_add_paddle_fields
Create Date: 2026-02-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0012_add_price_to_plans'
down_revision = '0011_add_paddle_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('plans', sa.Column('price', sa.Numeric(10, 2), nullable=True))
    op.add_column('plans', sa.Column('currency', sa.String(3), nullable=True, server_default='USD'))


def downgrade() -> None:
    op.drop_column('plans', 'currency')
    op.drop_column('plans', 'price')
