"""migrate order statuses to new values

Revision ID: c4d5e6f7a8b9
Revises: a1b2c3d4e5f7
Create Date: 2026-05-30

Summary:
  - ACCEPTED  → CONFIRMED
  - DELIVERED → COMPLETED
  - REJECTED  → CANCELLED
"""

from alembic import op

revision = 'c4d5e6f7a8b9'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE orders SET status = 'CONFIRMED' WHERE status = 'ACCEPTED'")
    op.execute("UPDATE orders SET status = 'COMPLETED' WHERE status = 'DELIVERED'")
    op.execute("UPDATE orders SET status = 'CANCELLED' WHERE status = 'REJECTED'")


def downgrade() -> None:
    op.execute("UPDATE orders SET status = 'ACCEPTED'  WHERE status = 'CONFIRMED'")
    op.execute("UPDATE orders SET status = 'DELIVERED' WHERE status = 'COMPLETED'")
    op.execute("UPDATE orders SET status = 'REJECTED'  WHERE status = 'CANCELLED'")
