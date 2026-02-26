from typing import List
from sqlalchemy.orm import Session
from src.models.chat_message import ChatMessage
from src.repositories.base_repository import BaseRepository

class ChatMessageRepository(BaseRepository[ChatMessage]):
    """Repository for ChatMessage model."""
    
    def __init__(self, session: Session):
        super().__init__(ChatMessage, session)

    def get_user_history(self, user_id: int, limit: int = 50) -> List[ChatMessage]:
        return self.session.query(ChatMessage)\
            .filter(ChatMessage.user_id == user_id)\
            .order_by(ChatMessage.created_at.desc())\
            .limit(limit).all()
