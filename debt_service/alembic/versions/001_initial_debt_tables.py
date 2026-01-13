"""Initial debt tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create contacts table
    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contacts_id'), 'contacts', ['id'], unique=False)
    op.create_index(op.f('ix_contacts_user_id'), 'contacts', ['user_id'], unique=False)

    # Create debts table
    op.create_table(
        'debts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),  # Will be made nullable in next migration
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('debt_type', sa.String(length=50), nullable=False),
        sa.Column('initial_amount', sa.Float(), nullable=False),
        sa.Column('current_balance', sa.Float(), nullable=False),
        sa.Column('interest_rate', sa.Float(), nullable=True),
        sa.Column('minimum_payment', sa.Float(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('last_payment_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.Column('is_paid_off', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_debts_id'), 'debts', ['id'], unique=False)
    op.create_index(op.f('ix_debts_user_id'), 'debts', ['user_id'], unique=False)

    # Create debt_payments table
    op.create_table(
        'debt_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('debt_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('principal_amount', sa.Float(), nullable=True),
        sa.Column('interest_amount', sa.Float(), nullable=True),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['debt_id'], ['debts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_debt_payments_id'), 'debt_payments', ['id'], unique=False)
    op.create_index(op.f('ix_debt_payments_user_id'), 'debt_payments', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_debt_payments_user_id'), table_name='debt_payments')
    op.drop_index(op.f('ix_debt_payments_id'), table_name='debt_payments')
    op.drop_table('debt_payments')
    op.drop_index(op.f('ix_debts_user_id'), table_name='debts')
    op.drop_index(op.f('ix_debts_id'), table_name='debts')
    op.drop_table('debts')
    op.drop_index(op.f('ix_contacts_user_id'), table_name='contacts')
    op.drop_index(op.f('ix_contacts_id'), table_name='contacts')
    op.drop_table('contacts')

