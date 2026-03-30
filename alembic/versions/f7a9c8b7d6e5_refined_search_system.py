"""Refined Search System - Add FTS, Trigram, and Trends

Revision ID: f7a9c8b7d6e5
Revises: e1a2b3c4d5f6
Create Date: 2026-03-30 14:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f7a9c8b7d6e5'
down_revision: Union[str, Sequence[str], None] = 'e1a2b3c4d5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pg_trgm for fuzzy matching
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # 1. Update search_history
    op.add_column('search_history', 
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True)
    )
    # Deduplicate before adding unique constraint
    op.execute("""
        DELETE FROM search_history a USING search_history b
        WHERE a.id < b.id AND a.user_id = b.user_id AND a.query = b.query
    """)
    op.create_unique_constraint('unique_user_query', 'search_history', ['user_id', 'query'])

    # 2. Create search_trends table
    op.create_table('search_trends',
        sa.Column('query', sa.String(), nullable=False),
        sa.Column('count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('last_searched_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('query')
    )
    op.create_index(op.f('ix_search_trends_query'), 'search_trends', ['query'], unique=False)

    # 3. Update places for FTS
    op.add_column('places', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True))
    
    # Create GIN indexes
    op.execute("CREATE INDEX idx_places_search_vector ON places USING GIN(search_vector)")
    op.execute("CREATE INDEX idx_places_trgm ON places USING GIN(name gin_trgm_ops)")
    # B-tree index with text_pattern_ops for optimized prefix search
    op.execute("CREATE INDEX idx_places_name_prefix ON places (name text_pattern_ops)")

    # Backfill search_vector
    op.execute("""
        UPDATE places p
        SET search_vector = (
            setweight(to_tsvector('english', p.name), 'A') ||
            setweight(to_tsvector('english', coalesce(c.name, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(p.description, '')), 'C')
        )
        FROM categories c
        WHERE p.category_id = c.id;
    """)


def downgrade() -> None:
    op.drop_column('places', 'search_vector')
    op.execute("DROP INDEX IF EXISTS idx_places_search_vector")
    op.execute("DROP INDEX IF EXISTS idx_places_trgm")
    op.execute("DROP INDEX IF EXISTS idx_places_name_prefix")
    
    op.drop_index(op.f('ix_search_trends_query'), table_name='search_trends')
    op.drop_table('search_trends')
    
    op.drop_constraint('unique_user_query', 'search_history', type_='unique')
    op.drop_column('search_history', 'updated_at')
