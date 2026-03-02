"""add updated_at to favorites

Revision ID: c7f3a1b2d4e5
Revises: aeb553ae1f87
Create Date: 2026-03-02 09:28:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7f3a1b2d4e5'
down_revision: Union[str, Sequence[str], None] = 'aeb553ae1f87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add updated_at column to favorites table."""
    op.add_column(
        'favorites',
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Remove updated_at column from favorites table."""
    op.drop_column('favorites', 'updated_at')
