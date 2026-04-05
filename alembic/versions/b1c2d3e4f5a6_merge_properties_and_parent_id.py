"""Merge properties and parent_id branches

Revision ID: b1c2d3e4f5a6
Revises: f8a9c8b7d6e6, a5a6b7947dfa
Create Date: 2026-04-05 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = ('f8a9c8b7d6e6', 'a5a6b7947dfa')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge heads - no schema changes needed."""
    pass


def downgrade() -> None:
    """Merge heads - no schema changes needed."""
    pass
