"""enforce_place_ownership_and_add_index

Revision ID: 13c809a82c24
Revises: a0656d1812f5
Create Date: 2026-03-03 19:39:05.555452

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13c809a82c24'
down_revision: Union[str, Sequence[str], None] = 'a0656d1812f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Ensure existing places are owned by an ADMIN (as requested)
    op.execute("""
        UPDATE places 
        SET owner_id = (
            COALESCE(
                (SELECT id FROM users WHERE role = 'ADMIN' ORDER BY id LIMIT 1),
                (SELECT id FROM users ORDER BY id LIMIT 1)
            )
        )
        WHERE owner_id IS NULL
    """)

    # 2. Add index on owner_id
    op.create_index(op.f('ix_places_owner_id'), 'places', ['owner_id'], unique=False)

    # 3. Conversations and Messages (Missing from AI Integration phase)
    op.create_table('conversations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_id'), 'conversations', ['id'], unique=False)
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('sender', sa.String(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_conversations_id'), table_name='conversations')
    op.drop_table('conversations')
    op.drop_index(op.f('ix_places_owner_id'), table_name='places')
