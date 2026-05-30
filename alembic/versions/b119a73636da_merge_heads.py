"""merge heads

Revision ID: b119a73636da
Revises: b3c4d5e6f7a8, c4d5e6f7a8b9
Create Date: 2026-05-30 20:24:08.107115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b119a73636da'
down_revision: Union[str, Sequence[str], None] = ('b3c4d5e6f7a8', 'c4d5e6f7a8b9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
