"""add is_open to places

Revision ID: f6a7b8c9d0e1
Revises: 14fbf4c0e601
Create Date: 2026-06-28

"""
from alembic import op
import sqlalchemy as sa

revision = 'f6a7b8c9d0e1'
down_revision = '14fbf4c0e601'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('places')]
    if 'is_open' not in columns:
        op.add_column(
            'places',
            sa.Column('is_open', sa.Boolean(), nullable=False, server_default=sa.text('true'))
        )


def downgrade():
    op.drop_column('places', 'is_open')
