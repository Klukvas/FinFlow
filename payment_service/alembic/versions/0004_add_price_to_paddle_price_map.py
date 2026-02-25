"""Add price and currency to paddle_price_map for server-side validation

Revision ID: 0004_add_price_validation
Revises: 0003_add_paddle_support
Create Date: 2026-02-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004_add_price_validation'
down_revision = '0003_add_paddle_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('paddle_price_map', sa.Column('amount', sa.Numeric(10, 2), nullable=True))
    op.add_column('paddle_price_map', sa.Column('currency', sa.String(3), nullable=True, server_default='USD'))


def downgrade() -> None:
    op.drop_column('paddle_price_map', 'currency')
    op.drop_column('paddle_price_map', 'amount')
