"""Backfill workspace_id for existing goals

Revision ID: 0004_backfill_workspace_id
Revises: 0003_add_workspace_id
Create Date: 2025-01-27 15:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import httpx
import os

# revision identifiers, used by Alembic.
revision = '0004_backfill_workspace_id'
down_revision = '0003_add_workspace_id'
branch_labels = None
depends_on = None


def get_user_default_workspace(user_id: int) -> str:
    """Get user's default workspace from workspace_service"""
    workspace_service_url = os.getenv('WORKSPACE_SERVICE_URL', 'http://workspace_service:8000')
    internal_token = os.getenv('INTERNAL_SECRET_TOKEN', '')
    
    try:
        headers = {"X-Internal-Token": internal_token} if internal_token else {}
        url = f"{workspace_service_url}/internal/users/{user_id}/default-workspace"
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("workspace_id")
    except Exception as e:
        print(f"Error getting default workspace for user {user_id}: {e}")
    
    return None


def upgrade() -> None:
    """Backfill workspace_id for existing goals"""
    connection = op.get_bind()
    
    # Get all distinct user_ids that have goals without workspace_id
    result = connection.execute(
        sa.text("SELECT DISTINCT user_id FROM goals WHERE workspace_id IS NULL")
    )
    user_ids = [row[0] for row in result]
    
    print(f"Found {len(user_ids)} users with goals needing workspace_id")
    
    for user_id in user_ids:
        workspace_id = get_user_default_workspace(user_id)
        
        if workspace_id:
            connection.execute(
                sa.text(
                    "UPDATE goals SET workspace_id = :workspace_id WHERE user_id = :user_id AND workspace_id IS NULL"
                ),
                {"workspace_id": workspace_id, "user_id": user_id}
            )
            print(f"Updated goals for user {user_id} with workspace {workspace_id}")
        else:
            print(f"WARNING: Could not find default workspace for user {user_id}")


def downgrade() -> None:
    # No need to do anything on downgrade
    pass

