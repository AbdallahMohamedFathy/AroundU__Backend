"""add hashed_refresh_token to users

Revision ID: aeb553ae1f87
Revises: 1305b2680acf
Create Date: 2026-02-27 09:23:54.065885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aeb553ae1f87'
down_revision: Union[str, Sequence[str], None] = '1305b2680acf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("hashed_refresh_token", sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "hashed_refresh_token")
