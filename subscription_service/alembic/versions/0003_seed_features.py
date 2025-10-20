from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = '0003_seed_features'
down_revision = '0002_seed_basic_plan'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Insert features
    op.execute(
        """
        INSERT INTO features (code, name, description) VALUES
        ('categories', 'Categories', 'Number of categories user can create'),
        ('accounts', 'Accounts', 'Number of accounts user can create'),
        ('expenses', 'Expenses', 'Number of expenses user can create'),
        ('incomes', 'Incomes', 'Number of incomes user can create'),
        ('debts', 'Debts', 'Number of debts user can create'),
        ('recurring', 'Recurring Transactions', 'Number of recurring transactions user can create'),
        ('goals', 'Goals', 'Number of goals user can create')
        ON CONFLICT (code) DO NOTHING;
        """
    )

    # Insert basic plan restrictions
    op.execute(
        """
        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, f.code, true, 
            CASE f.code
                WHEN 'categories' THEN 16
                WHEN 'accounts' THEN 3
                WHEN 'expenses' THEN 1000
                WHEN 'incomes' THEN 1000
                WHEN 'debts' THEN 3
                WHEN 'recurring' THEN 2
                WHEN 'goals' THEN 3
            END
        FROM plans p, features f
        WHERE p.code = 'basic'
        ON CONFLICT (plan_id, feature_code) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM plan_features WHERE plan_id = (SELECT id FROM plans WHERE code = 'basic');")
    op.execute("DELETE FROM features WHERE code IN ('categories', 'accounts', 'expenses', 'incomes', 'debts', 'recurring', 'goals');")
