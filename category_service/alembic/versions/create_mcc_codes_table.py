"""create_mcc_codes_table

Revision ID: create_mcc
Revises: e138e7a86b02
Create Date: 2025-04-10 17:44:21.379185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'create_mcc'
down_revision: Union[str, None] = 'e138e7a86b02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create mcc_codes and translations tables."""
    op.create_table(
        'mcc_codes',
        sa.Column('mcc_code', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),  # canonical English name
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('mcc_code')
    )

    op.create_table(
        'translations',
        sa.Column('mcc_code', sa.Integer(), nullable=False),
        sa.Column('lang', sa.String(5), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['mcc_code'], ['mcc_codes.mcc_code'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('mcc_code', 'lang')
    )


def downgrade() -> None:
    """Drop mcc_codes and translations tables."""
    op.drop_table('translations')
    op.drop_table('mcc_codes')