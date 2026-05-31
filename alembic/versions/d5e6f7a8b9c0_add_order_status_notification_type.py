"""Add ORDER_STATUS to notificationtype enum

Revision ID: d5e6f7a8b9c0
Revises: b119a73636da
Create Date: 2026-05-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'b119a73636da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'ORDER_STATUS'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values without recreating the type.
    pass
