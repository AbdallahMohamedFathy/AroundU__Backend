"""convert property contact_number to array

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-10 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Alter the column type to ARRAY(String)
    # Using 'USING' clause to handle existing data if any
    op.execute('ALTER TABLE properties ALTER COLUMN contact_number TYPE varchar[] USING CASE WHEN contact_number IS NULL THEN NULL ELSE ARRAY[contact_number] END')


def downgrade() -> None:
    # Convert back to single string (takes first element if exists)
    op.execute('ALTER TABLE properties ALTER COLUMN contact_number TYPE varchar USING CASE WHEN contact_number IS NULL THEN NULL ELSE contact_number[1] END')
