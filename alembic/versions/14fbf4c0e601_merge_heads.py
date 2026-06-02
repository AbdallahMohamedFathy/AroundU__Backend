"""merge heads

Revision ID: 14fbf4c0e601
Revises: a1b2c3d4e5fa, d5e6f7a8b9c0, e2f3a4b5c6d7
Create Date: 2026-06-02 19:08:32.380951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14fbf4c0e601'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5fa', 'd5e6f7a8b9c0', 'e2f3a4b5c6d7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
