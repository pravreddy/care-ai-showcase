"""Add OAuth fields to users table

Revision ID: 002_add_oauth_fields
Revises: 001_initial_schema
Create Date: 2026-03-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_oauth_fields'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add OAuth columns
    op.add_column('users', sa.Column('auth_provider', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('provider_user_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('picture_url', sa.String(1000), nullable=True))

    # Make hashed_password nullable (OAuth users don't have passwords)
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(255),
                    nullable=True)

    # Index for fast OAuth lookups
    op.create_index(
        'ix_users_provider_lookup',
        'users',
        ['auth_provider', 'provider_user_id'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('ix_users_provider_lookup', table_name='users')
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(255),
                    nullable=False)
    op.drop_column('users', 'picture_url')
    op.drop_column('users', 'provider_user_id')
    op.drop_column('users', 'auth_provider')
