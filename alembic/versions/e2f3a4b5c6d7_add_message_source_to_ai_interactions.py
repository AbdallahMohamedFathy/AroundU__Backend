"""add message_source to ai_interactions

Revision ID: e2f3a4b5c6d7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-02

"""
from alembic import op
import sqlalchemy as sa

revision = "e2f3a4b5c6d7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "ai_interactions",
        sa.Column("message_source", sa.String(10), nullable=True, server_default="text"),
    )


def downgrade():
    op.drop_column("ai_interactions", "message_source")
