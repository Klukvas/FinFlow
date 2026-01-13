"""backfill workspace_id from user personal workspaces

Revision ID: 005
Revises: 004
Create Date: 2025-12-20 14:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import httpx
import os

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_user_default_workspace(user_id: int) -> str:
    """Get user's default workspace ID from workspace_service"""
    workspace_service_url = os.getenv('WORKSPACE_SERVICE_URL', 'http://workspace_service:8000')
    internal_token = os.getenv('INTERNAL_SECRET_TOKEN', '')
    
    try:
        url = f"{workspace_service_url}/internal/users/{user_id}/default-workspace"
        headers = {
            "X-Internal-Token": internal_token,
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('workspace_id')
            else:
                print(f"Warning: Could not get default workspace for user {user_id}: {response.status_code}")
                return None
    except Exception as e:
        print(f"Error getting default workspace for user {user_id}: {e}")
        return None


def upgrade() -> None:
    """
    Backfill workspace_id for all existing categories.
    
    For each user, get their personal workspace ID and assign it to all their categories.
    """
    connection = op.get_bind()
    
    # Get all unique user_ids
    result = connection.execute(sa.text("SELECT DISTINCT user_id FROM categories WHERE workspace_id IS NULL"))
    user_ids = [row[0] for row in result]
    
    print(f"Found {len(user_ids)} users with categories needing workspace_id")
    
    # For each user, get their default workspace and update their categories
    for user_id in user_ids:
        workspace_id = get_user_default_workspace(user_id)
        
        if workspace_id:
            print(f"Updating categories for user {user_id} with workspace {workspace_id}")
            connection.execute(
                sa.text("UPDATE categories SET workspace_id = :workspace_id WHERE user_id = :user_id AND workspace_id IS NULL"),
                {"workspace_id": workspace_id, "user_id": user_id}
            )
        else:
            print(f"Warning: Could not get workspace for user {user_id}, skipping")


def downgrade() -> None:
    """Downgrade: Clear workspace_id values"""
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE categories SET workspace_id = NULL"))


