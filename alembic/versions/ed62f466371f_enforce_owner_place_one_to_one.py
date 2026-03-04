"""enforce owner place one to one

Revision ID: ed62f466371f
Revises: 3639a7390027
Create Date: 2026-03-04 11:20:01.177755

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed62f466371f'
down_revision: Union[str, Sequence[str], None] = '3639a7390027'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add owner_id as nullable first
    op.add_column('places', sa.Column('owner_id', sa.Integer(), nullable=True))
    
    # 2. Backfill existing places with users
    connection = op.get_bind()
    
    # Check if there are places
    places_count = connection.execute(sa.text("SELECT count(*) FROM places")).scalar()
    
    if places_count > 0:
        # Since we must enforce ONE-TO-ONE, we delete all places except the oldest one
        # to ensure no constraints are violated during a messy migration of test data.
        # Then, we assign the remaining place to the first available admin.
        connection.execute(sa.text("""
            WITH first_place AS (
                SELECT id FROM places ORDER BY created_at ASC LIMIT 1
            )
            DELETE FROM places WHERE id NOT IN (SELECT id FROM first_place);
        """))
        
        # Get an admin ID
        admin_result = connection.execute(sa.text("SELECT id FROM users WHERE role = 'ADMIN' LIMIT 1")).fetchone()
        
        if not admin_result:
            # If no admin exists, we must create a dummy user to satisfy the foreign key and not null constraint
            connection.execute(sa.text("""
                INSERT INTO users (full_name, email, password_hash, role, is_active, is_verified)
                VALUES ('Migration Admin', 'migration@admin.com', 'dummy_hash', 'ADMIN', true, true)
            """))
            admin_result = connection.execute(sa.text("SELECT id FROM users WHERE email = 'migration@admin.com'")).fetchone()
            
        admin_id = admin_result[0]
        
        # Assign the remaining place to the admin
        connection.execute(sa.text("UPDATE places SET owner_id = :admin_id WHERE owner_id IS NULL"), {"admin_id": admin_id})
        
    # 3. Make the column NOT NULL 
    op.alter_column('places', 'owner_id', nullable=False)
    
    # 4. Create the foreign key and unique index
    op.create_foreign_key('fk_places_owner_id_users', 'places', 'users', ['owner_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_places_owner_id'), 'places', ['owner_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_places_owner_id'), table_name='places')
    op.drop_constraint('fk_places_owner_id_users', 'places', type_='foreignkey')
    op.drop_column('places', 'owner_id')
