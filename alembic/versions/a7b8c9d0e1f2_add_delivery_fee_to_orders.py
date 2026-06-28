"""add delivery_fee to orders

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-29

"""
from alembic import op
import sqlalchemy as sa

revision = 'a7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('orders')]
    if 'delivery_fee' not in columns:
        op.add_column(
            'orders',
            sa.Column('delivery_fee', sa.Float(), nullable=False, server_default=sa.text('0.0'))
        )


def downgrade():
    op.drop_column('orders', 'delivery_fee')
