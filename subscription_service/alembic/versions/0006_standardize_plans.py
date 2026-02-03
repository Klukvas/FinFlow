from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = '0006_standardize_plans'
down_revision = '0005_unique_user_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Standardize subscription plans to exactly 3 monthly plans:
    - Basic (free)
    - Professional (paid)
    - Enterprise (paid)
    
    Each plan has specific feature limits.
    """
    
    # Step 1: Delete old plan_features to avoid foreign key conflicts
    op.execute("DELETE FROM plan_features;")
    
    # Step 2: Update existing plans or insert new ones
    # We use INSERT ... ON CONFLICT to handle cases where plans already exist
    op.execute("""
        -- Insert/Update Basic plan
        INSERT INTO plans (code, name, period_days, is_active, version, created_at, updated_at)
        VALUES ('basic', 'Basic', 30, TRUE, 1, NOW(), NOW())
        ON CONFLICT (code) DO UPDATE SET 
            name = EXCLUDED.name,
            period_days = EXCLUDED.period_days,
            is_active = EXCLUDED.is_active,
            updated_at = NOW();
        
        -- Insert/Update Professional plan
        INSERT INTO plans (code, name, period_days, is_active, version, created_at, updated_at)
        VALUES ('professional', 'Professional', 30, TRUE, 1, NOW(), NOW())
        ON CONFLICT (code) DO UPDATE SET 
            name = EXCLUDED.name,
            period_days = EXCLUDED.period_days,
            is_active = EXCLUDED.is_active,
            updated_at = NOW();
        
        -- Insert/Update Enterprise plan
        INSERT INTO plans (code, name, period_days, is_active, version, created_at, updated_at)
        VALUES ('enterprise', 'Enterprise', 30, TRUE, 1, NOW(), NOW())
        ON CONFLICT (code) DO UPDATE SET 
            name = EXCLUDED.name,
            period_days = EXCLUDED.period_days,
            is_active = EXCLUDED.is_active,
            updated_at = NOW();
    """)
    
    # Step 3: Migrate any subscriptions from old plan codes to new ones
    # Map: pro-monthly -> professional, pro-yearly -> professional
    op.execute("""
        UPDATE subscriptions 
        SET plan_code = 'professional' 
        WHERE plan_code IN ('pro-monthly', 'pro-yearly');
    """)
    
    # Step 4: Delete old plans that are no longer valid
    op.execute("""
        DELETE FROM plans 
        WHERE code NOT IN ('basic', 'professional', 'enterprise');
    """)
    
    # Step 5: Define feature limits for each plan
    
    # BASIC PLAN - Free tier with limited features
    op.execute("""
        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, f.code, true,
            CASE f.code
                WHEN 'categories' THEN 10          -- 10 categories total
                WHEN 'accounts' THEN 2             -- 2 accounts total
                WHEN 'expenses' THEN 50            -- 50 expenses per calendar month
                WHEN 'incomes' THEN 50             -- 50 incomes per calendar month
                WHEN 'debts' THEN 2                -- 2 debts total
                WHEN 'recurring' THEN 3            -- 3 recurring transactions total
                WHEN 'goals' THEN 2                -- 2 goals total
                WHEN 'workspaces' THEN 1           -- 1 workspace only
            END
        FROM plans p
        CROSS JOIN features f
        WHERE p.code = 'basic'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;
    """)
    
    # PROFESSIONAL PLAN - Mid-tier for individuals and small businesses
    op.execute("""
        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, f.code, true,
            CASE f.code
                WHEN 'categories' THEN 50          -- 50 categories total
                WHEN 'accounts' THEN 10            -- 10 accounts total
                WHEN 'expenses' THEN 5000          -- 5000 expenses per calendar month
                WHEN 'incomes' THEN 5000           -- 5000 incomes per calendar month
                WHEN 'debts' THEN 20               -- 20 debts total
                WHEN 'recurring' THEN 50           -- 50 recurring transactions total
                WHEN 'goals' THEN 20               -- 20 goals total
                WHEN 'workspaces' THEN 3           -- 3 workspaces total
            END
        FROM plans p
        CROSS JOIN features f
        WHERE p.code = 'professional'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;
    """)
    
    # ENTERPRISE PLAN - Unlimited for large organizations
    op.execute("""
        INSERT INTO plan_features (plan_id, feature_code, enabled, limit_value)
        SELECT p.id, f.code, true,
            CASE f.code
                WHEN 'categories' THEN NULL        -- Unlimited categories
                WHEN 'accounts' THEN NULL          -- Unlimited accounts
                WHEN 'expenses' THEN NULL          -- Unlimited expenses per month
                WHEN 'incomes' THEN NULL           -- Unlimited incomes per month
                WHEN 'debts' THEN NULL             -- Unlimited debts
                WHEN 'recurring' THEN NULL         -- Unlimited recurring transactions
                WHEN 'goals' THEN NULL             -- Unlimited goals
                WHEN 'workspaces' THEN 10          -- 10 workspaces total
            END
        FROM plans p
        CROSS JOIN features f
        WHERE p.code = 'enterprise'
        ON CONFLICT (plan_id, feature_code) DO UPDATE SET
            enabled = EXCLUDED.enabled,
            limit_value = EXCLUDED.limit_value;
    """)


def downgrade() -> None:
    """Rollback to previous state"""
    # This is a complex migration, so downgrade just removes the new plans
    op.execute("DELETE FROM plan_features;")
    op.execute("DELETE FROM plans WHERE code IN ('basic', 'professional', 'enterprise');")
