"""Fix search_vector: use simple language config and add auto-update trigger

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f7
Create Date: 2026-05-29 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rebuild search_vector using 'simple' config so Arabic (and any language)
    #    words are stored as-is without English-only stemming/stop-word removal.
    op.execute("""
        UPDATE places p
        SET search_vector = (
            setweight(to_tsvector('simple', p.name), 'A') ||
            setweight(to_tsvector('simple', coalesce(c.name, '')), 'B') ||
            setweight(to_tsvector('simple', coalesce(p.description, '')), 'C')
        )
        FROM categories c
        WHERE p.category_id = c.id
    """)

    # 2. Create trigger function that keeps search_vector in sync on INSERT/UPDATE.
    op.execute("""
        CREATE OR REPLACE FUNCTION places_search_vector_update()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('simple', coalesce(NEW.name, '')), 'A') ||
                setweight(to_tsvector('simple', coalesce(
                    (SELECT name FROM categories WHERE id = NEW.category_id), ''
                )), 'B') ||
                setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 3. Attach trigger to places table.
    op.execute("""
        DROP TRIGGER IF EXISTS trig_places_search_vector ON places;
        CREATE TRIGGER trig_places_search_vector
        BEFORE INSERT OR UPDATE OF name, description, category_id
        ON places
        FOR EACH ROW EXECUTE FUNCTION places_search_vector_update();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trig_places_search_vector ON places")
    op.execute("DROP FUNCTION IF EXISTS places_search_vector_update()")

    # Revert search_vector back to 'english' config.
    op.execute("""
        UPDATE places p
        SET search_vector = (
            setweight(to_tsvector('english', p.name), 'A') ||
            setweight(to_tsvector('english', coalesce(c.name, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(p.description, '')), 'C')
        )
        FROM categories c
        WHERE p.category_id = c.id
    """)
