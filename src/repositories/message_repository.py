from typing import List
from sqlalchemy.orm import Session
from src.models.message import Message
from src.repositories.base_repository import BaseRepository

class MessageRepository(BaseRepository[Message]):
    """Repository for Message model."""
    
    def __init__(self, session: Session):
        super().__init__(Message, session)

    def get_by_conversation(self, conversation_id: int) -> List[Message]:
        return self.session.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.timestamp.asc()).all()
