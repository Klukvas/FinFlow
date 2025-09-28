"""Initial migration for recurring payments

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

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
    # Create recurring_payments table
    op.create_table('recurring_payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('category_id', postgresql.Integer(), nullable=False),
        sa.Column('payment_type', sa.Enum('EXPENSE', 'INCOME', name='payment_type_enum'), nullable=False),
        sa.Column('schedule_type', sa.Enum('daily', 'weekly', 'monthly', 'yearly', name='schedule_type_enum'), nullable=False),
        sa.Column('schedule_config', sa.JSON(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.Enum('active', 'paused', 'completed', 'cancelled', name='status_enum'), nullable=False),
        sa.Column('last_executed', sa.DateTime(), nullable=True),
        sa.Column('next_execution', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recurring_payments_user_id'), 'recurring_payments', ['user_id'], unique=False)

    # Create payment_schedules table
    op.create_table('payment_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recurring_payment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'executed', 'failed', name='schedule_status_enum'), nullable=False),
        sa.Column('created_expense_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_income_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['recurring_payment_id'], ['recurring_payments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('payment_schedules')
    op.drop_index(op.f('ix_recurring_payments_user_id'), table_name='recurring_payments')
    op.drop_table('recurring_payments')
    op.execute('DROP TYPE IF EXISTS payment_type_enum')
    op.execute('DROP TYPE IF EXISTS schedule_type_enum')
    op.execute('DROP TYPE IF EXISTS status_enum')
    op.execute('DROP TYPE IF EXISTS schedule_status_enum')
