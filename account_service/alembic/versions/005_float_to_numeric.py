"""Convert float columns to numeric for monetary precision

Revision ID: 005
Revises: 004
Create Date: 2026-02-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE accounts ALTER COLUMN balance TYPE NUMERIC(12,2) USING balance::numeric(12,2)")


def downgrade() -> None:
    op.execute("ALTER TABLE accounts ALTER COLUMN balance TYPE DOUBLE PRECISION USING balance::double precision")
