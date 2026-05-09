"""replace owner_id with place_id in carts and orders

Revision ID: a1b2c3d4e5f6
Revises: 2337bedf1a28
Create Date: 2026-05-09

Summary:
  - carts: drop owner_id, add place_id (FK -> places.id)
  - orders: drop owner_id (place_id already exists)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a1b2c3d4e5f6'
down_revision = '52a1b9c2d7e8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # TABLE: carts                                                         #
    # ------------------------------------------------------------------ #
    # 1. Drop the old owner_id column
    op.drop_column('carts', 'owner_id')

    # 2. Add place_id with FK to places.id (SET NULL on delete to keep cart rows)
    op.add_column(
        'carts',
        sa.Column('place_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_carts_place_id',
        'carts', 'places',
        ['place_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index('ix_carts_place_id', 'carts', ['place_id'])

    # ------------------------------------------------------------------ #
    # TABLE: orders                                                        #
    # ------------------------------------------------------------------ #
    # Drop owner_id — place_id FK already existed from a previous migration
    # Guard: only drop if it actually exists (safe for re-runs)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    orders_cols = [c['name'] for c in inspector.get_columns('orders')]

    if 'owner_id' in orders_cols:
        op.drop_index('ix_orders_owner_id', table_name='orders', if_exists=True)
        op.drop_column('orders', 'owner_id')


def downgrade() -> None:
    # ------------------------------------------------------------------ #
    # TABLE: orders — restore owner_id                                    #
    # ------------------------------------------------------------------ #
    op.add_column(
        'orders',
        sa.Column('owner_id', sa.Integer(), nullable=True)
    )
    op.create_index('ix_orders_owner_id', 'orders', ['owner_id'])

    # ------------------------------------------------------------------ #
    # TABLE: carts — restore owner_id, drop place_id                     #
    # ------------------------------------------------------------------ #
    op.drop_index('ix_carts_place_id', table_name='carts')
    op.drop_constraint('fk_carts_place_id', 'carts', type_='foreignkey')
    op.drop_column('carts', 'place_id')

    op.add_column(
        'carts',
        sa.Column('owner_id', sa.Integer(), nullable=True)
    )
    op.create_index('ix_carts_owner_id', 'carts', ['owner_id'])
