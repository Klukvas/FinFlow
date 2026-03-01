"""update basic plan limits and enable ai for free tier

Revision ID: 0015_update_basic_plan_limits
Revises: 0014_add_ai_assistant_feature
Create Date: 2026-03-01 00:00:00.000000

"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = '0015_update_basic_plan_limits'
down_revision = '0014_add_ai_assistant_feature'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Update Basic plan limits:
    - categories: 10 → 5
    - recurring: 3 → 1
    - pdf_uploads_per_month: 1 → 2
    - pdf_records_per_upload: 20 → 40
    - ai_assistant: disabled → enabled with limit_value=2

    Also set limit_value for Pro (10) and Business/Enterprise (15) AI quotas.
    """

    # Categories: 10 → 5
    op.execute("""
        UPDATE plan_features SET limit_value = 5
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
          AND feature_code = 'categories';
    """)

    # Recurring: 3 → 1
    op.execute("""
        UPDATE plan_features SET limit_value = 1
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
          AND feature_code = 'recurring';
    """)

    # PDF uploads per month: 1 → 2
    op.execute("""
        UPDATE plan_features SET limit_value = 2
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
          AND feature_code = 'pdf_uploads_per_month';
    """)

    # PDF records per upload: 20 → 40
    op.execute("""
        UPDATE plan_features SET limit_value = 40
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
          AND feature_code = 'pdf_records_per_upload';
    """)

    # AI assistant: enable for Basic with limit_value=2
    op.execute("""
        UPDATE plan_features SET enabled = true, limit_value = 2
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
          AND feature_code = 'ai_assistant';
    """)

    # AI assistant: set limit_value for Professional (was hardcoded in service)
    op.execute("""
        UPDATE plan_features SET limit_value = 10
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'professional')
          AND feature_code = 'ai_assistant';
    """)

    # AI assistant: set limit_value for Enterprise (was hardcoded in service)
    op.execute("""
        UPDATE plan_features SET limit_value = 15
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'enterprise')
          AND feature_code = 'ai_assistant';
    """)


def downgrade() -> None:
    """Revert Basic plan limits and AI assistant changes."""

    # Categories: 5 → 10
    op.execute("""
        UPDATE plan_features SET limit_value = 10
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
          AND feature_code = 'categories';
    """)

    # Recurring: 1 → 3
    op.execute("""
        UPDATE plan_features SET limit_value = 3
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
          AND feature_code = 'recurring';
    """)

    # PDF uploads per month: 2 → 1
    op.execute("""
        UPDATE plan_features SET limit_value = 1
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
          AND feature_code = 'pdf_uploads_per_month';
    """)

    # PDF records per upload: 40 → 20
    op.execute("""
        UPDATE plan_features SET limit_value = 20
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
          AND feature_code = 'pdf_records_per_upload';
    """)

    # AI assistant: disable for Basic, remove limit_value
    op.execute("""
        UPDATE plan_features SET enabled = false, limit_value = NULL
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
          AND feature_code = 'ai_assistant';
    """)

    # AI assistant: remove limit_value for Professional (was hardcoded)
    op.execute("""
        UPDATE plan_features SET limit_value = NULL
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'professional')
          AND feature_code = 'ai_assistant';
    """)

    # AI assistant: remove limit_value for Enterprise (was hardcoded)
    op.execute("""
        UPDATE plan_features SET limit_value = NULL
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'enterprise')
          AND feature_code = 'ai_assistant';
    """)
