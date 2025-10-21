"""Initial goals and milestones tables

Revision ID: 0001_initial
Revises: 
Create Date: 2025-01-27 12:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create goals table
    op.create_table('goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('goal_type', sa.Enum('SAVINGS', 'DEBT_PAYOFF', 'INVESTMENT', 'EXPENSE_REDUCTION', 'INCOME_INCREASE', 'EMERGENCY_FUND', name='goaltype'), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='goalpriority'), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED', name='goalstatus'), nullable=True),
        sa.Column('target_amount', sa.Float(), nullable=False),
        sa.Column('current_amount', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('target_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.Column('is_milestone_based', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goals_id'), 'goals', ['id'], unique=False)
    op.create_index(op.f('ix_goals_user_id'), 'goals', ['user_id'], unique=False)

    # Create milestones table
    op.create_table('milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_amount', sa.Float(), nullable=False),
        sa.Column('current_amount', sa.Float(), nullable=True),
        sa.Column('target_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_milestones_id'), 'milestones', ['id'], unique=False)
    op.create_index(op.f('ix_milestones_goal_id'), 'milestones', ['goal_id'], unique=False)


def downgrade() -> None:
    # Drop milestones table first (due to foreign key constraint)
    op.drop_index(op.f('ix_milestones_goal_id'), table_name='milestones')
    op.drop_index(op.f('ix_milestones_id'), table_name='milestones')
    op.drop_table('milestones')
    
    # Drop goals table
    op.drop_index(op.f('ix_goals_user_id'), table_name='goals')
    op.drop_index(op.f('ix_goals_id'), table_name='goals')
    op.drop_table('goals')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS goaltype')
    op.execute('DROP TYPE IF EXISTS goalpriority')
    op.execute('DROP TYPE IF EXISTS goalstatus')
