"""add image_url to cart and order items

Revision ID: a1b2c3d4e5f7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-10 02:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add columns to cart_items
    op.add_column('cart_items', sa.Column('item_name', sa.String(), nullable=True))
    op.add_column('cart_items', sa.Column('image_url', sa.String(), nullable=True))
    
    # Add columns to order_items
    op.add_column('order_items', sa.Column('image_url', sa.String(), nullable=True))

def downgrade() -> None:
    # Drop columns from order_items
    op.drop_column('order_items', 'image_url')
    
    # Drop columns from cart_items
    op.drop_column('cart_items', 'image_url')
    op.drop_column('cart_items', 'item_name')
