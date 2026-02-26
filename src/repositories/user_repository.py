from typing import Optional
from sqlalchemy.orm import Session
from src.models.user import User
from src.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    """Repository for User model."""
    
    def __init__(self, session: Session):
        super().__init__(User, session)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter(User.email == email).first()

    def get_by_verification_token(self, token: str) -> Optional[User]:
        return self.session.query(User).filter(User.verification_token == token).first()

    def get_by_reset_token(self, token: str) -> Optional[User]:
        return self.session.query(User).filter(User.reset_token == token).first()
