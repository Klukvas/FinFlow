from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = '0002_seed_basic_plan'
down_revision = '0001_init'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO plans (code, name, period_days, is_active, version, created_at, updated_at)
        VALUES ('basic', 'Basic', 30, TRUE, 1, NOW(), NOW())
        ON CONFLICT (code) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM plans WHERE code = 'basic';")


