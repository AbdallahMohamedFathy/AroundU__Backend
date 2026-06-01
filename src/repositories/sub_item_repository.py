from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.sub_item import SubItem
from src.repositories.base_repository import BaseRepository


class SubItemRepository(BaseRepository[SubItem]):
    def __init__(self, session: Session):
        super().__init__(SubItem, session)

    def get_by_id(self, id: int) -> Optional[SubItem]:
        return self.session.query(self.model).filter(
            self.model.id == id,
            self.model.is_deleted == False
        ).first()

    def get_by_item(self, item_id: int) -> List[SubItem]:
        return self.session.query(self.model).filter(
            self.model.item_id == item_id,
            self.model.is_deleted == False
        ).order_by(self.model.created_at.asc()).all()

    def get_by_name_and_item(self, name: str, item_id: int) -> Optional[SubItem]:
        return self.session.query(self.model).filter(
            self.model.name == name,
            self.model.item_id == item_id,
            self.model.is_deleted == False
        ).first()
