"""add ai_assistant feature

Revision ID: 0014_add_ai_assistant_feature
Revises: 0013_processed_events
Create Date: 2026-02-27 00:00:00.000000

"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = '0014_add_ai_assistant_feature'
down_revision = '0013_processed_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add ai_assistant feature for AI-powered financial analysis.

    Plan access:
    - Basic: disabled
    - Professional: enabled
    - Enterprise: enabled
    """

    # Step 1: Add feature to features table
    op.execute("""
        INSERT INTO features (code, name, description)
        VALUES
            ('ai_assistant', 'AI Financial Assistant',
             'AI-powered financial analysis with personalized recommendations')
        ON CONFLICT (code) DO NOTHING;
    """)

    # Step 2: Basic plan - disabled
    op.execute("""
        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, 'ai_assistant', false, NULL
        FROM plans p
        WHERE p.code = 'basic'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;
    """)

    # Step 3: Professional plan - enabled
    op.execute("""
        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, 'ai_assistant', true, NULL
        FROM plans p
        WHERE p.code = 'professional'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;
    """)

    # Step 4: Enterprise plan - enabled
    op.execute("""
        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, 'ai_assistant', true, NULL
        FROM plans p
        WHERE p.code = 'enterprise'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;
    """)


def downgrade() -> None:
    """Remove AI assistant feature"""
    op.execute("""
        DELETE FROM plan_features
        WHERE feature_code = 'ai_assistant';
    """)
    op.execute("""
        DELETE FROM features
        WHERE code = 'ai_assistant';
    """)
