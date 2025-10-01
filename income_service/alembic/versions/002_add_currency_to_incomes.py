"""add_currency_to_incomes

Revision ID: 002_add_currency_to_incomes
Revises: 001_add_account_id_to_incomes
Create Date: 2025-10-01 23:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_currency_to_incomes'
down_revision: Union[str, None] = '001_add_account_id_to_incomes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add column as nullable first
    op.add_column('incomes', sa.Column('currency', sa.String(length=3), nullable=True))
    
    # Update existing records to have default currency
    op.execute("UPDATE incomes SET currency = 'USD' WHERE currency IS NULL")
    
    # Now make the column NOT NULL
    op.alter_column('incomes', 'currency', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('incomes', 'currency')
