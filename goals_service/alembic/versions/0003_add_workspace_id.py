"""Add workspace_id to goals table

Revision ID: 0003_add_workspace_id
Revises: 24615e35e6d3
Create Date: 2025-01-27 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003_add_workspace_id'
down_revision = '24615e35e6d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add workspace_id column as nullable first
    op.add_column('goals', sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create indexes
    op.create_index('idx_goals_workspace_id', 'goals', ['workspace_id'], unique=False)
    op.create_index('idx_goals_workspace_user', 'goals', ['workspace_id', 'user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_goals_workspace_user', table_name='goals')
    op.drop_index('idx_goals_workspace_id', table_name='goals')
    op.drop_column('goals', 'workspace_id')

