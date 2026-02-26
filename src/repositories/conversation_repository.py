from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.conversation import Conversation
from src.repositories.base_repository import BaseRepository

class ConversationRepository(BaseRepository[Conversation]):
    """Repository for Conversation model."""
    
    def __init__(self, session: Session):
        super().__init__(Conversation, session)

    def get_latest_for_user(self, user_id: int) -> Optional[Conversation]:
        return self.session.query(Conversation)\
            .filter(Conversation.user_id == user_id)\
            .order_by(Conversation.created_at.desc()).first()
