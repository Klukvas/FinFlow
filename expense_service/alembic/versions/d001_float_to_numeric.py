"""Convert float columns to numeric for monetary precision

Revision ID: d001_float_to_numeric
Revises: 010
Create Date: 2026-02-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd001_float_to_numeric'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE expenses ALTER COLUMN amount TYPE NUMERIC(12,2) USING amount::numeric(12,2)")


def downgrade() -> None:
    op.execute("ALTER TABLE expenses ALTER COLUMN amount TYPE DOUBLE PRECISION USING amount::double precision")
