"""Add consent and cancellation fields

Revision ID: 0008_consent_cancellation
Revises: 0007_add_recurring_fields
Create Date: 2026-01-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008_consent_cancellation'
down_revision = '0007_add_recurring_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add consent fields to subscriptions table
    op.add_column('subscriptions', sa.Column('consent_given', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('subscriptions', sa.Column('consent_version', sa.String(length=16), nullable=True))
    op.add_column('subscriptions', sa.Column('consent_timestamp', sa.DateTime(), nullable=True))
    op.add_column('subscriptions', sa.Column('consent_ip_address', sa.String(length=45), nullable=True))
    op.add_column('subscriptions', sa.Column('consent_user_agent', sa.Text(), nullable=True))
    
    # Add cancellation fields to subscriptions table
    op.add_column('subscriptions', sa.Column('cancellation_reason', sa.String(length=32), nullable=True))
    op.add_column('subscriptions', sa.Column('cancellation_comment', sa.Text(), nullable=True))
    op.add_column('subscriptions', sa.Column('cancellation_ip_address', sa.String(length=45), nullable=True))
    
    # Create subscription_consent_log table for audit trail
    op.create_table(
        'subscription_consent_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=128), nullable=False),
        sa.Column('consent_version', sa.String(length=16), nullable=False),
        sa.Column('consent_text', sa.Text(), nullable=False),
        sa.Column('consent_language', sa.String(length=8), nullable=False),
        sa.Column('consent_given_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('browser_fingerprint', sa.String(length=64), nullable=True),
        sa.Column('consent_metadata', sa.JSON(), nullable=True),  # Renamed from 'metadata' (reserved in SQLAlchemy)
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_consent_log_user', 'subscription_consent_log', ['user_id'], unique=False)
    op.create_index('idx_consent_log_subscription', 'subscription_consent_log', ['subscription_id'], unique=False)
    op.create_index('idx_consent_log_created', 'subscription_consent_log', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_consent_log_created', table_name='subscription_consent_log')
    op.drop_index('idx_consent_log_subscription', table_name='subscription_consent_log')
    op.drop_index('idx_consent_log_user', table_name='subscription_consent_log')
    
    # Drop consent log table
    op.drop_table('subscription_consent_log')
    
    # Drop cancellation fields
    op.drop_column('subscriptions', 'cancellation_ip_address')
    op.drop_column('subscriptions', 'cancellation_comment')
    op.drop_column('subscriptions', 'cancellation_reason')
    
    # Drop consent fields
    op.drop_column('subscriptions', 'consent_user_agent')
    op.drop_column('subscriptions', 'consent_ip_address')
    op.drop_column('subscriptions', 'consent_timestamp')
    op.drop_column('subscriptions', 'consent_version')
    op.drop_column('subscriptions', 'consent_given')
