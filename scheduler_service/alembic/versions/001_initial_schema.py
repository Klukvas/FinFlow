"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create job_executions table
    op.create_table(
        'job_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_name', sa.String(length=128), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'SKIPPED', name='jobstatus'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('items_processed', sa.Integer(), nullable=True),
        sa.Column('items_succeeded', sa.Integer(), nullable=True),
        sa.Column('items_failed', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_executions_job_name'), 'job_executions', ['job_name'], unique=False)

    # Create renewal_attempts table
    op.create_table(
        'renewal_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=128), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.String(length=32), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('attempt_number', sa.Integer(), nullable=True),
        sa.Column('extra_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_renewal_attempts_job_execution_id'), 'renewal_attempts', ['job_execution_id'], unique=False)
    op.create_index(op.f('ix_renewal_attempts_subscription_id'), 'renewal_attempts', ['subscription_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_renewal_attempts_subscription_id'), table_name='renewal_attempts')
    op.drop_index(op.f('ix_renewal_attempts_job_execution_id'), table_name='renewal_attempts')
    op.drop_table('renewal_attempts')
    op.drop_index(op.f('ix_job_executions_job_name'), table_name='job_executions')
    op.drop_table('job_executions')
    op.execute('DROP TYPE jobstatus')
