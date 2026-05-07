from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from src.models.item import Item
from src.repositories.base_repository import BaseRepository

class ItemRepository(BaseRepository[Item]):
    def __init__(self, session: Session):
        super().__init__(Item, session)

    def get_by_subcategory(self, sub_category_id: int) -> List[Item]:
        return self.session.query(self.model).filter(
            self.model.sub_category_id == sub_category_id,
            self.model.is_deleted == False
        ).all()

    def get_by_name_and_subcategory(self, name: str, sub_category_id: int) -> Optional[Item]:
        return self.session.query(self.model).filter(
            self.model.name == name,
            self.model.sub_category_id == sub_category_id,
            self.model.is_deleted == False
        ).first()

    def search_items(
        self, 
        name: Optional[str] = None, 
        skip: int = 0, 
        limit: int = 10,
        sub_category_id: Optional[int] = None
    ) -> Tuple[List[Item], int]:
        query = self.session.query(self.model).filter(self.model.is_deleted == False)
        
        if name:
            query = query.filter(self.model.name.ilike(f"%{name}%"))
        
        if sub_category_id:
            query = query.filter(self.model.sub_category_id == sub_category_id)
            
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return items, total
