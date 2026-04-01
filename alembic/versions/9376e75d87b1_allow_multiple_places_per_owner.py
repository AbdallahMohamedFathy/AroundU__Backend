"""allow_multiple_places_per_owner

Revision ID: 9376e75d87b1
Revises: a5cd4ba8d725
Create Date: 2026-04-01 20:43:58.039358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9376e75d87b1'
down_revision: Union[str, Sequence[str], None] = 'a5cd4ba8d725'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Remove unique constraint on owner_id."""
    # Drop unique constraint if exists (Postgres naming convention)
    op.execute("ALTER TABLE places DROP CONSTRAINT IF EXISTS places_owner_id_key")
    # Drop unique index if exists
    op.execute("DROP INDEX IF EXISTS ix_places_owner_id")
    # Re-create index as non-unique
    op.create_index(op.f('ix_places_owner_id'), 'places', ['owner_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema: Restore unique constraint on owner_id."""
    # This might fail if there are already multiple places per owner
    op.drop_index(op.f('ix_places_owner_id'), table_name='places')
    op.create_index(op.f('ix_places_owner_id'), 'places', ['owner_id'], unique=True)
