"""create pdf_uploads table

Revision ID: 001
Revises:
Create Date: 2026-01-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create pdf_uploads table for tracking upload history and enforcing monthly limits.

    Table structure follows the same pattern as expense/income services with:
    - Composite index on (user_id, created_at) for monthly limit queries
    - Timestamps (created_at, updated_at) for tracking
    - Status tracking for upload success/failure
    """
    op.create_table(
        'pdf_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('total_transactions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_parses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_parses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='success'),
        sa.Column('created_at', sa.DateTime(), server_default=func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_pdf_uploads_id', 'pdf_uploads', ['id'], unique=False)
    op.create_index('ix_pdf_uploads_user_id', 'pdf_uploads', ['user_id'], unique=False)

    # CRITICAL: Composite index for monthly limit queries
    # Enables fast filtering: WHERE user_id = X AND created_at >= month_start
    op.create_index(
        'idx_pdf_uploads_user_created',
        'pdf_uploads',
        ['user_id', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    """Drop pdf_uploads table and all indexes"""
    op.drop_index('idx_pdf_uploads_user_created', table_name='pdf_uploads')
    op.drop_index('ix_pdf_uploads_user_id', table_name='pdf_uploads')
    op.drop_index('ix_pdf_uploads_id', table_name='pdf_uploads')
    op.drop_table('pdf_uploads')
