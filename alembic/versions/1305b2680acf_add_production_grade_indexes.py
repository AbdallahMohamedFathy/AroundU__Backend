"""Add production-grade indexes

Revision ID: 1305b2680acf
Revises: 0002f24253f0
Create Date: 2026-02-26 07:26:06.114227

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1305b2680acf'
down_revision: Union[str, Sequence[str], None] = '0002f24253f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Location indexing for optimized bounding box searches
    op.create_index('idx_places_location', 'places', ['latitude', 'longitude'])
    
    # Foreign key indexing to prevent full table scans on joins
    op.create_index('idx_places_category_id', 'places', ['category_id'])
    op.create_index('idx_reviews_place_id', 'reviews', ['place_id'])
    op.create_index('idx_reviews_user_id', 'reviews', ['user_id'])
    op.create_index('idx_favorites_user_id', 'favorites', ['user_id'])
    op.create_index('idx_search_history_user_id', 'search_history', ['user_id'])
    op.create_index('idx_chat_messages_user_id', 'chat_messages', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_chat_messages_user_id', table_name='chat_messages')
    op.drop_index('idx_search_history_user_id', table_name='search_history')
    op.drop_index('idx_favorites_user_id', table_name='favorites')
    op.drop_index('idx_reviews_user_id', table_name='reviews')
    op.drop_index('idx_reviews_place_id', table_name='reviews')
    op.drop_index('idx_places_category_id', table_name='places')
    op.drop_index('idx_places_location', table_name='places')
