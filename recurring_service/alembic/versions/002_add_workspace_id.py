"""add workspace_id to recurring_payments

Revision ID: 002b
Revises: 002
Create Date: 2025-12-23 22:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002b'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add workspace_id to recurring_payments table"""
    # Add workspace_id column (nullable for now)
    op.add_column('recurring_payments', sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create indexes
    op.create_index('idx_recurring_payments_workspace_id', 'recurring_payments', ['workspace_id'], unique=False)
    op.create_index('idx_recurring_payments_workspace_user', 'recurring_payments', ['workspace_id', 'user_id'], unique=False)


def downgrade() -> None:
    """Remove workspace_id from recurring_payments"""
    op.drop_index('idx_recurring_payments_workspace_user', table_name='recurring_payments')
    op.drop_index('idx_recurring_payments_workspace_id', table_name='recurring_payments')
    op.drop_column('recurring_payments', 'workspace_id')


