"""Add favorites, reviews, place_images and enhance user/place models

Revision ID: 0002_add_new_features
Revises: f34f7b4e8048
Create Date: 2026-02-21

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "0002_add_new_features"
down_revision: Union[str, None] = "f34f7b4e8048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enhance users table ───────────────────────────────────
    op.add_column("users", sa.Column("role", sa.String(), nullable=False, server_default="user"))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("verification_token", sa.String(), nullable=True))
    op.add_column("users", sa.Column("reset_token", sa.String(), nullable=True))
    op.add_column("users", sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    # ── Enhance places table ──────────────────────────────────
    op.add_column("places", sa.Column("address", sa.String(), nullable=True))
    op.add_column("places", sa.Column("phone", sa.String(), nullable=True))
    op.add_column("places", sa.Column("website", sa.String(), nullable=True))
    op.add_column("places", sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("places", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("places", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True))
    op.add_column("places", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    # ── Create place_images table ─────────────────────────────
    op.create_table(
        "place_images",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("place_id", sa.Integer(), sa.ForeignKey("places.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
    )

    # ── Create favorites table ────────────────────────────────
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("place_id", sa.Integer(), sa.ForeignKey("places.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.UniqueConstraint("user_id", "place_id", name="unique_user_place_favorite"),
    )

    # ── Create reviews table ──────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("place_id", sa.Integer(), sa.ForeignKey("places.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Update chat_messages FK to CASCADE ────────────────────
    # (SQLite does not support ALTER CONSTRAINT, skip for SQLite)
    with op.batch_alter_table("search_history") as batch_op:
        batch_op.drop_constraint("search_history_user_id_fkey", type_="foreignkey") if op.get_bind().dialect.name != "sqlite" else None

    with op.batch_alter_table("chat_messages") as batch_op:
        batch_op.drop_constraint("chat_messages_user_id_fkey", type_="foreignkey") if op.get_bind().dialect.name != "sqlite" else None


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("favorites")
    op.drop_table("place_images")

    for col in ["address", "phone", "website", "review_count", "is_active", "created_at", "updated_at"]:
        op.drop_column("places", col)

    for col in ["role", "is_active", "is_verified", "verification_token", "reset_token", "reset_token_expires", "updated_at"]:
        op.drop_column("users", col)
