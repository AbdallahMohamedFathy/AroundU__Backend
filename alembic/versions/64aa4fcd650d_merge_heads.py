"""merge heads

Revision ID: 64aa4fcd650d
Revises: 3639a7390027, c7f3a1b2d4e5
Create Date: 2026-03-02 10:52:45.927509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64aa4fcd650d'
down_revision: Union[str, Sequence[str], None] = ('3639a7390027', 'c7f3a1b2d4e5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
