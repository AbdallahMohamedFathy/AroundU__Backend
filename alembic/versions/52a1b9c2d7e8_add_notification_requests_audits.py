"""add notification request and audit system

Revision ID: 52a1b9c2d7e8
Revises: 7aa967586e2f
Create Date: 2026-04-11 13:28:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '52a1b9c2d7e8'
down_revision: Union[str, None] = '7aa967586e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Notification Requests Table
    op.create_table(
        'notification_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.Enum('ALL_USERS', 'ALL_OWNERS', 'SPECIFIC_OWNER', 'SPECIFIC_USER', name='notification_target_type'), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='notification_request_status'), server_default='PENDING', nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default='False', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_notification_requests_id'), 'notification_requests', ['id'], unique=False)
    
    # Notification Audits Table
    op.create_table(
        'notification_audits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.Enum('APPROVED', 'REJECTED', name='notification_audit_action'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['request_id'], ['notification_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_notification_audits_id'), 'notification_audits', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_notification_audits_id'), table_name='notification_audits')
    op.drop_table('notification_audits')
    op.drop_index(op.f('ix_notification_requests_id'), table_name='notification_requests')
    op.drop_table('notification_requests')
    
    op.execute("DROP TYPE IF EXISTS notification_target_type CASCADE")
    op.execute("DROP TYPE IF EXISTS notification_request_status CASCADE")
    op.execute("DROP TYPE IF EXISTS notification_audit_action CASCADE")
