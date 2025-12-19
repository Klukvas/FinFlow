"""Initial workspace tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workspaces table
    op.create_table(
        'workspaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.Enum('personal', 'shared', name='workspacetype'), nullable=False),
        sa.Column('owner_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_workspaces_owner_user_id', 'workspaces', ['owner_user_id'])
    op.create_index('ix_workspaces_archived_at', 'workspaces', ['archived_at'])

    # Create workspace_members table
    op.create_table(
        'workspace_members',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Enum('owner', 'admin', 'member', 'viewer', name='memberrole'), nullable=False),
        sa.Column('status', sa.Enum('active', 'left', 'removed', name='memberstatus'), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('ix_workspace_members_user_id', 'workspace_members', ['user_id'])
    op.create_index('ix_workspace_members_workspace_id', 'workspace_members', ['workspace_id'])
    op.create_unique_constraint('uq_workspace_member', 'workspace_members', ['workspace_id', 'user_id'])

    # Create workspace_invites table
    op.create_table(
        'workspace_invites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('inviter_user_id', sa.Integer(), nullable=False),
        sa.Column('invitee_user_id', sa.Integer(), nullable=True),
        sa.Column('invitee_email', sa.String(255), nullable=True),
        sa.Column('token_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('pending', 'accepted', 'revoked', 'expired', name='invitestatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_workspace_invites_token_hash', 'workspace_invites', ['token_hash'])
    op.create_index('ix_workspace_invites_workspace_id', 'workspace_invites', ['workspace_id'])
    op.create_index('ix_workspace_invites_invitee_email', 'workspace_invites', ['invitee_email'])


def downgrade() -> None:
    op.drop_table('workspace_invites')
    op.drop_table('workspace_members')
    op.drop_table('workspaces')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS invitestatus')
    op.execute('DROP TYPE IF EXISTS memberstatus')
    op.execute('DROP TYPE IF EXISTS memberrole')
    op.execute('DROP TYPE IF EXISTS workspacetype')

