"""Convert enums to strings

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert workspaces.type from enum to VARCHAR
    op.execute("ALTER TABLE workspaces ALTER COLUMN type TYPE VARCHAR(50) USING type::text")
    
    # Convert workspace_members.role from enum to VARCHAR
    op.execute("ALTER TABLE workspace_members ALTER COLUMN role TYPE VARCHAR(50) USING role::text")
    
    # Convert workspace_members.status from enum to VARCHAR
    op.execute("ALTER TABLE workspace_members ALTER COLUMN status TYPE VARCHAR(50) USING status::text")
    
    # Convert workspace_invites.status from enum to VARCHAR
    op.execute("ALTER TABLE workspace_invites ALTER COLUMN status TYPE VARCHAR(50) USING status::text")
    
    # Drop the enum types (they're no longer needed)
    op.execute('DROP TYPE IF EXISTS workspacetype')
    op.execute('DROP TYPE IF EXISTS memberrole')
    op.execute('DROP TYPE IF EXISTS memberstatus')
    op.execute('DROP TYPE IF EXISTS invitestatus')


def downgrade() -> None:
    # Recreate enum types
    op.execute("CREATE TYPE workspacetype AS ENUM ('personal', 'shared')")
    op.execute("CREATE TYPE memberrole AS ENUM ('owner', 'admin', 'member', 'viewer')")
    op.execute("CREATE TYPE memberstatus AS ENUM ('active', 'left', 'removed')")
    op.execute("CREATE TYPE invitestatus AS ENUM ('pending', 'accepted', 'revoked', 'expired')")
    
    # Convert back to enums
    op.execute("ALTER TABLE workspaces ALTER COLUMN type TYPE workspacetype USING type::workspacetype")
    op.execute("ALTER TABLE workspace_members ALTER COLUMN role TYPE memberrole USING role::memberrole")
    op.execute("ALTER TABLE workspace_members ALTER COLUMN status TYPE memberstatus USING status::memberstatus")
    op.execute("ALTER TABLE workspace_invites ALTER COLUMN status TYPE invitestatus USING status::invitestatus")

