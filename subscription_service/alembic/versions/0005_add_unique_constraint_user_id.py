from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005_unique_user_id'
down_revision = '0004_add_workspaces_feature'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add unique constraint on user_id in subscriptions table.
    
    First, clean up any duplicate subscriptions by keeping only the most recent one per user.
    """
    
    # Step 1: Delete duplicate subscriptions, keeping only the one with the highest id (most recent)
    # This SQL finds duplicate user_ids and deletes all but the one with max(id)
    op.execute("""
        DELETE FROM subscriptions
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM subscriptions
            GROUP BY user_id
        );
    """)
    
    # Step 2: Add unique constraint on user_id
    op.create_unique_constraint('uq_subscriptions_user_id', 'subscriptions', ['user_id'])


def downgrade() -> None:
    """Remove the unique constraint"""
    op.drop_constraint('uq_subscriptions_user_id', 'subscriptions', type_='unique')
