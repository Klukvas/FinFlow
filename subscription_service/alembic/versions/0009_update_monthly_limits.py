from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = '0009_update_monthly_limits'
down_revision = '0008_consent_cancellation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Update expense and income limits to monthly limits (50 per month for basic, 5000 for professional).
    This migration updates the existing plan_features to reflect the new monthly limit strategy.
    """

    # Update BASIC plan: expenses and incomes from 100 to 50 (monthly limit)
    op.execute("""
        UPDATE plan_features
        SET limit_value = 50
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
        AND feature_code IN ('expenses', 'incomes');
    """)

    # Professional and Enterprise plans keep their existing values
    # (5000 for professional, NULL for enterprise)
    # No changes needed for other features


def downgrade() -> None:
    """Rollback to previous limits"""

    # Restore BASIC plan: expenses and incomes back to 100
    op.execute("""
        UPDATE plan_features
        SET limit_value = 100
        WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic')
        AND feature_code IN ('expenses', 'incomes');
    """)
