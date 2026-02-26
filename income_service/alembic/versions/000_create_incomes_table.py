"""create incomes table

Revision ID: 000_create_incomes_table
Revises:
Create Date: 2025-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '000_create_incomes_table'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'incomes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('date', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incomes_id'), 'incomes', ['id'], unique=False)
    op.create_index(op.f('ix_incomes_user_id'), 'incomes', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_incomes_user_id'), table_name='incomes')
    op.drop_index(op.f('ix_incomes_id'), table_name='incomes')
    op.drop_table('incomes')
