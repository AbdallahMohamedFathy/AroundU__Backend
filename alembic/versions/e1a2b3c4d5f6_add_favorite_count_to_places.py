"""Add favorite_count to places for recommendation engine

Revision ID: e1a2b3c4d5f6
Revises: d31eb022e1f2
Create Date: 2026-03-30 10:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1a2b3c4d5f6'
down_revision: Union[str, Sequence[str], None] = 'd31eb022e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add favorite_count column and backfill from existing favorites."""
    # 1. Add the column with a safe default
    op.add_column(
        'places',
        sa.Column('favorite_count', sa.Integer(), nullable=False, server_default='0')
    )

    # 2. Backfill from existing favorites table
    op.execute("""
        UPDATE places
        SET favorite_count = sub.cnt
        FROM (
            SELECT place_id, COUNT(*) AS cnt
            FROM favorites
            GROUP BY place_id
        ) AS sub
        WHERE places.id = sub.place_id
    """)

    # 3. Add index for sorting by popularity
    op.create_index('ix_places_favorite_count', 'places', ['favorite_count'])


def downgrade() -> None:
    """Remove favorite_count column."""
    op.drop_index('ix_places_favorite_count', table_name='places')
    op.drop_column('places', 'favorite_count')
