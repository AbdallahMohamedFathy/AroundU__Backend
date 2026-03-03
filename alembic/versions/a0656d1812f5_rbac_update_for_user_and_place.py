"""rbac update for user and place

Revision ID: a0656d1812f5
Revises: 3d08122de8e0
Create Date: 2026-03-03 16:53:07.876529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a0656d1812f5'
down_revision: Union[str, Sequence[str], None] = '3d08122de8e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Update users table - role column
    # Convert Enum to String
    op.alter_column('users', 'role',
               existing_type=postgresql.ENUM('USER', 'ADMIN', 'MODERATOR', name='userrole'),
               type_=sa.String(),
               existing_nullable=False,
               postgresql_using="role::text")
    
    # 2. Update places table - owner_id column
    # Add as nullable first
    op.add_column('places', sa.Column('owner_id', sa.Integer(), nullable=True))
    
    # Assign a default owner (the first user in the DB) to existing places
    op.execute("UPDATE places SET owner_id = (SELECT id FROM users LIMIT 1) WHERE owner_id IS NULL")
    
    # Now make it NOT NULL
    op.alter_column('places', 'owner_id', nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key('fk_places_owner', 'places', 'users', ['owner_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Revert places table changes
    op.drop_constraint('fk_places_owner', 'places', type_='foreignkey')
    op.drop_column('places', 'owner_id')

    # 2. Revert users table changes
    op.alter_column('users', 'role',
               existing_type=sa.String(),
               type_=postgresql.ENUM('USER', 'ADMIN', 'MODERATOR', name='userrole'),
               existing_nullable=False,
               postgresql_using="role::userrole")
