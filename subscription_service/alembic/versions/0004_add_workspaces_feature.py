"""Add workspaces feature

Revision ID: 0004_add_workspaces_feature
Revises: 0003_seed_features
Create Date: 2025-01-27

"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = '0004_add_workspaces_feature'
down_revision = '0003_seed_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Insert workspaces feature
    op.execute(
        """
        INSERT INTO features (code, name, description) VALUES
        ('workspaces', 'Workspaces', 'Number of workspaces user can create')
        ON CONFLICT (code) DO NOTHING;
        """
    )

    # Add workspaces limit to basic plan (1 workspace by default)
    op.execute(
        """
        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, 'workspaces', true, 1
        FROM plans p
        WHERE p.code = 'basic'
        ON CONFLICT (plan_id, feature_code) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM plan_features WHERE feature_code = 'workspaces';")
    op.execute("DELETE FROM features WHERE code = 'workspaces';")

