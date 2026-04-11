"""Add fcm and notifications

Revision ID: 7aa967586e2f
Revises: d4e5f6a7b8c9
Create Date: 2026-04-11 14:49:53.555768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7aa967586e2f'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add fcm_token to users
    op.add_column('users', sa.Column('fcm_token', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_fcm_token'), 'users', ['fcm_token'], unique=False)

    # Create notifications table
    # Enum types are automatically created by sa.Enum
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.Enum('NEW_REVIEW', 'NEW_PROPERTY_REVIEW', 'PROPERTY_APPROVED', 'PROPERTY_REJECTED', 'SYSTEM_ALERT', name='notificationtype'), nullable=False),
        sa.Column('priority', sa.Enum('NORMAL', 'HIGH', name='notificationpriority'), nullable=False, server_default='NORMAL'),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index('ix_notifications_user_read', 'notifications', ['user_id', 'is_read'], unique=False)
    op.create_index('ix_notifications_created_at_desc', 'notifications', [sa.text('created_at DESC')], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    from sqlalchemy.dialects import postgresql

    op.drop_index('ix_notifications_created_at_desc', table_name='notifications')
    op.drop_index('ix_notifications_user_read', table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')

    op.drop_index(op.f('ix_users_fcm_token'), table_name='users')
    op.drop_column('users', 'fcm_token')

    postgresql.ENUM(name='notificationtype').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name='notificationpriority').drop(op.get_bind(), checkfirst=True)
