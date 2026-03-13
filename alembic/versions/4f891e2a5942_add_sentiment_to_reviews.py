"""add sentiment to reviews

Revision ID: 4f891e2a5942
Revises: 2337bedf1a28
Create Date: 2026-03-13 10:52:44.978210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f891e2a5942'
down_revision: Union[str, Sequence[str], None] = '2337bedf1a28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('reviews', sa.Column('sentiment', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('reviews', 'sentiment')
