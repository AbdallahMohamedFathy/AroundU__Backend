"""Merge multiple heads

Revision ID: 2337bedf1a28
Revises: 13c809a82c24, ed62f466371f
Create Date: 2026-03-13 01:25:48.679273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2337bedf1a28'
down_revision: Union[str, Sequence[str], None] = ('13c809a82c24', 'ed62f466371f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
