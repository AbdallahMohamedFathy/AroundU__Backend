"""add refined properties

Revision ID: f8a9c8b7d6e6
Revises: f7a9c8b7d6e5
Create Date: 2026-04-05 19:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f8a9c8b7d6e6'
down_revision: Union[str, Sequence[str], None] = 'f7a9c8b7d6e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create properties table
    op.create_table('properties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('main_image_url', sa.String(), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_properties_id'), 'properties', ['id'], unique=False)
    op.create_index(op.f('ix_properties_price'), 'properties', ['price'], unique=False)
    op.create_index(op.f('ix_properties_title'), 'properties', ['title'], unique=False)
    op.create_index(op.f('ix_properties_owner_id'), 'properties', ['owner_id'], unique=False)

    # 2. Create property_images table
    op.create_table('property_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_property_images_id'), 'property_images', ['id'], unique=False)
    op.create_index(op.f('ix_property_images_property_id'), 'property_images', ['property_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_property_images_property_id'), table_name='property_images')
    op.drop_index(op.f('ix_property_images_id'), table_name='property_images')
    op.drop_table('property_images')
    op.drop_index(op.f('ix_properties_title'), table_name='properties')
    op.drop_index(op.f('ix_properties_price'), table_name='properties')
    op.drop_index(op.f('ix_properties_owner_id'), table_name='properties')
    op.drop_index(op.f('ix_properties_id'), table_name='properties')
    op.drop_table('properties')
