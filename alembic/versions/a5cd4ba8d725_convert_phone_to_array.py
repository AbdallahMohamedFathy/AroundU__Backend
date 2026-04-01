"""convert_phone_to_array

Revision ID: a5cd4ba8d725
Revises: f7a9c8b7d6e5
Create Date: 2026-04-01 16:48:20.646950

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5cd4ba8d725'
down_revision: Union[str, Sequence[str], None] = 'f7a9c8b7d6e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    """Upgrade schema: Convert phone string to ARRAY(TEXT)."""
    # Use op.execute for PostgreSQL specific 'USING' clause
    op.execute("ALTER TABLE places ALTER COLUMN phone TYPE TEXT[] USING CASE WHEN phone IS NULL OR phone = '' THEN ARRAY[]::TEXT[] ELSE ARRAY[phone] END")

def downgrade() -> None:
    """Downgrade schema: Convert ARRAY(TEXT) back to string (comma separated)."""
    op.execute("ALTER TABLE places ALTER COLUMN phone TYPE VARCHAR USING array_to_string(phone, ',')")
