from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.category import Category
from src.repositories.base_repository import BaseRepository

class CategoryRepository(BaseRepository[Category]):
    """Repository for Category model."""
    
    def __init__(self, session: Session):
        super().__init__(Category, session)

    def get_by_name(self, name: str) -> Optional[Category]:
        return self.session.query(Category).filter(Category.name == name).first()
