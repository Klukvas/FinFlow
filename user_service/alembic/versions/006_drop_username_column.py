"""Drop username column from users table

Revision ID: 006_drop_username
Revises: 005_add_role_and_status
"""

from alembic import op
import sqlalchemy as sa

revision = '006_drop_username'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the unique index on username first
    op.drop_index('ix_users_username', table_name='users')
    # Drop the username column
    op.drop_column('users', 'username')


def downgrade():
    # Re-add username column as nullable (data is lost)
    op.add_column('users', sa.Column('username', sa.String(), nullable=True))
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
