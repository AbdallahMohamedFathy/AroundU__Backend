"""add sub_items table

Revision ID: a1b2c3d4e5fa
Revises: f8a9c8b7d6e6
Create Date: 2026-06-01

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5fa'
down_revision = 'f8a9c8b7d6e6'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table('sub_items'):
        op.create_table(
            'sub_items',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('price', sa.Numeric(10, 2), nullable=False),
            sa.Column('is_available', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('item_id', sa.Integer(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_sub_items_id', 'sub_items', ['id'])
        op.create_index('ix_sub_items_item_id', 'sub_items', ['item_id'])


def downgrade():
    op.drop_index('ix_sub_items_item_id', table_name='sub_items')
    op.drop_index('ix_sub_items_id', table_name='sub_items')
    op.drop_table('sub_items')
