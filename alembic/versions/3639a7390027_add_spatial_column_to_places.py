"""add_spatial_column_to_places

Revision ID: 3639a7390027
Revises: aeb553ae1f87
Create Date: 2026-02-27 14:55:52.314336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3639a7390027'
down_revision: Union[str, Sequence[str], None] = 'aeb553ae1f87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add geography column using raw SQL to avoid dependency issues during migration if needed
    op.execute("ALTER TABLE places ADD COLUMN location GEOGRAPHY(Point, 4326)")
    
    # Populate location column from existing latitude and longitude
    op.execute("UPDATE places SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography")
    
    # Add GIST index for high-performance spatial queries
    op.execute("CREATE INDEX idx_places_location_gist ON places USING GIST (location)")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_places_location_gist', table_name='places')
    op.drop_column('places', 'location')
