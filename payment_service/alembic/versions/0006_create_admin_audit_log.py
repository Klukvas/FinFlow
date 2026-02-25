"""Create admin_audit_log table

Revision ID: 0006_admin_audit
Revises: 0005_create_outbox
Create Date: 2026-02-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '0006_admin_audit'
down_revision = '0005_create_outbox'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'admin_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('admin_user_id', sa.String(128), nullable=False),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('resource_type', sa.String(64), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('details', JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_admin_audit_log_admin', 'admin_audit_log', ['admin_user_id'])
    op.create_index('idx_admin_audit_log_action', 'admin_audit_log', ['action', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_admin_audit_log_action')
    op.drop_index('idx_admin_audit_log_admin')
    op.drop_table('admin_audit_log')
