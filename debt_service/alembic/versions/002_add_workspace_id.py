"""add workspace_id to debts and contacts

Revision ID: 002
Revises: 8dfb3b1b990d
Create Date: 2025-12-23 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '8dfb3b1b990d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add workspace_id to debts and contacts tables"""
    # Add workspace_id to debts
    op.add_column('debts', sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('idx_debts_workspace_id', 'debts', ['workspace_id'], unique=False)
    op.create_index('idx_debts_workspace_user', 'debts', ['workspace_id', 'user_id'], unique=False)
    
    # Add workspace_id to contacts
    op.add_column('contacts', sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('idx_contacts_workspace_id', 'contacts', ['workspace_id'], unique=False)
    op.create_index('idx_contacts_workspace_user', 'contacts', ['workspace_id', 'user_id'], unique=False)


def downgrade() -> None:
    """Remove workspace_id from debts and contacts"""
    # Drop indexes and column from contacts
    op.drop_index('idx_contacts_workspace_user', table_name='contacts')
    op.drop_index('idx_contacts_workspace_id', table_name='contacts')
    op.drop_column('contacts', 'workspace_id')
    
    # Drop indexes and column from debts
    op.drop_index('idx_debts_workspace_user', table_name='debts')
    op.drop_index('idx_debts_workspace_id', table_name='debts')
    op.drop_column('debts', 'workspace_id')


