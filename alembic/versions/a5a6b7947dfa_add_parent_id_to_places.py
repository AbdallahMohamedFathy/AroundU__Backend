"""add_parent_id_to_places

Revision ID: a5a6b7947dfa
Revises: 9376e75d87b1
Create Date: 2026-04-04 09:00:19.906984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5a6b7947dfa'
down_revision: Union[str, Sequence[str], None] = '9376e75d87b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add parent_id column
    op.add_column('places', sa.Column('parent_id', sa.Integer(), nullable=True))
    
    # 2. Add foreign key constraint
    op.create_foreign_key(
        'fk_places_parent_id', 'places', 'places', ['parent_id'], ['id'], ondelete='SET NULL'
    )
    
    # 3. Create index
    op.create_index(op.f('ix_places_parent_id'), 'places', ['parent_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Drop index
    op.drop_index(op.f('ix_places_parent_id'), table_name='places')
    
    # 2. Drop foreign key
    op.drop_constraint('fk_places_parent_id', 'places', type_='foreignkey')
    
    # 3. Drop column
    op.drop_column('places', 'parent_id')
