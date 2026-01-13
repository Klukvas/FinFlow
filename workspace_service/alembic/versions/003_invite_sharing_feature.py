"""Invite sharing feature - simplified roles and in-app invitations

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 00:00:00.000000

This migration:
1. Simplifies member roles: owner, full (write), read
2. Updates invite statuses: pending, accepted, rejected, expired, canceled
3. Adds role column to invites (role assigned on acceptance)
4. Removes token_hash (in-app flow, no email tokens)
5. Makes invitee_user_id required (must be existing user)
6. Adds partial unique index for pending invites per workspace+user
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ========== 1. Update workspace_members roles ==========
    # Convert old roles to new simplified roles:
    # - 'owner' stays 'owner'
    # - 'admin' -> 'full' (had write access)
    # - 'member' -> 'full' (had write access)
    # - 'viewer' -> 'read' (had read-only access)
    op.execute("""
        UPDATE workspace_members 
        SET role = CASE 
            WHEN role = 'admin' THEN 'full'
            WHEN role = 'member' THEN 'full'
            WHEN role = 'viewer' THEN 'read'
            ELSE role
        END
    """)
    
    # ========== 2. Update workspace_invites statuses ==========
    # Convert 'revoked' to 'canceled' (owner canceled)
    op.execute("""
        UPDATE workspace_invites 
        SET status = 'canceled' 
        WHERE status = 'revoked'
    """)
    
    # ========== 3. Add role column to workspace_invites ==========
    op.add_column(
        'workspace_invites',
        sa.Column('role', sa.String(50), nullable=True)
    )
    # Set default role for existing invites
    op.execute("UPDATE workspace_invites SET role = 'read' WHERE role IS NULL")
    # Make it NOT NULL
    op.alter_column('workspace_invites', 'role', nullable=False)
    
    # ========== 4. Add responded_at timestamp ==========
    op.add_column(
        'workspace_invites',
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True)
    )
    # Set responded_at for already accepted/rejected invites
    op.execute("""
        UPDATE workspace_invites 
        SET responded_at = COALESCE(accepted_at, updated_at)
        WHERE status IN ('accepted', 'rejected', 'canceled')
    """)
    
    # ========== 5. Handle token_hash removal ==========
    # Drop the unique constraint and index on token_hash
    op.drop_index('ix_workspace_invites_token_hash', table_name='workspace_invites')
    # Drop the column
    op.drop_column('workspace_invites', 'token_hash')
    
    # ========== 6. Make invitee_user_id NOT NULL ==========
    # First, delete any invites without invitee_user_id (email-only invites)
    op.execute("DELETE FROM workspace_invites WHERE invitee_user_id IS NULL")
    # Now make it NOT NULL
    op.alter_column('workspace_invites', 'invitee_user_id', nullable=False)
    
    # ========== 7. Make invitee_email NOT NULL ==========
    # Set email from existing data or placeholder for old records
    op.execute("""
        UPDATE workspace_invites 
        SET invitee_email = 'unknown@placeholder.local' 
        WHERE invitee_email IS NULL
    """)
    op.alter_column('workspace_invites', 'invitee_email', nullable=False)
    
    # ========== 8. Add new indexes ==========
    # Index on invitee_user_id for "my invites" queries
    op.create_index(
        'ix_workspace_invites_invitee_user_id', 
        'workspace_invites', 
        ['invitee_user_id']
    )
    # Index on inviter_user_id
    op.create_index(
        'ix_workspace_invites_inviter_user_id', 
        'workspace_invites', 
        ['inviter_user_id']
    )
    # Index on status for filtering
    op.create_index(
        'ix_workspace_invites_status', 
        'workspace_invites', 
        ['status']
    )
    # Partial unique index: only one pending invite per workspace+user
    op.execute("""
        CREATE UNIQUE INDEX ix_workspace_invites_pending_unique 
        ON workspace_invites (workspace_id, invitee_user_id) 
        WHERE status = 'pending'
    """)


def downgrade() -> None:
    # Drop new indexes
    op.execute("DROP INDEX IF EXISTS ix_workspace_invites_pending_unique")
    op.drop_index('ix_workspace_invites_status', table_name='workspace_invites')
    op.drop_index('ix_workspace_invites_inviter_user_id', table_name='workspace_invites')
    op.drop_index('ix_workspace_invites_invitee_user_id', table_name='workspace_invites')
    
    # Restore token_hash column
    op.add_column(
        'workspace_invites',
        sa.Column('token_hash', sa.String(255), nullable=True)
    )
    # Generate placeholder tokens for existing records
    op.execute("""
        UPDATE workspace_invites 
        SET token_hash = 'legacy_' || id::text 
        WHERE token_hash IS NULL
    """)
    op.alter_column('workspace_invites', 'token_hash', nullable=False)
    op.create_index('ix_workspace_invites_token_hash', 'workspace_invites', ['token_hash'], unique=True)
    
    # Allow NULL invitee_user_id and invitee_email again
    op.alter_column('workspace_invites', 'invitee_user_id', nullable=True)
    op.alter_column('workspace_invites', 'invitee_email', nullable=True)
    
    # Drop responded_at column
    op.drop_column('workspace_invites', 'responded_at')
    
    # Drop role column
    op.drop_column('workspace_invites', 'role')
    
    # Revert invite statuses
    op.execute("""
        UPDATE workspace_invites 
        SET status = 'revoked' 
        WHERE status IN ('canceled', 'rejected')
    """)
    
    # Revert member roles
    op.execute("""
        UPDATE workspace_members 
        SET role = CASE 
            WHEN role = 'full' THEN 'member'
            WHEN role = 'read' THEN 'viewer'
            ELSE role
        END
    """)
