from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.subcategory import SubCategory
from src.repositories.base_repository import BaseRepository

class SubCategoryRepository(BaseRepository[SubCategory]):
    def __init__(self, session: Session):
        super().__init__(SubCategory, session)

    def get_by_place(self, place_id: int) -> List[SubCategory]:
        return self.session.query(self.model).filter(
            self.model.place_id == place_id,
            self.model.is_deleted == False
        ).all()

    def get_by_owner(self, owner_id: int) -> List[SubCategory]:
        return self.session.query(self.model).filter(
            self.model.owner_id == owner_id,
            self.model.is_deleted == False
        ).all()

    def get_by_name_and_owner(self, name: str, owner_id: int) -> Optional[SubCategory]:
        return self.session.query(self.model).filter(
            self.model.name == name,
            self.model.owner_id == owner_id,
            self.model.is_deleted == False
        ).first()

    def get_by_name_and_place(self, name: str, place_id: int) -> Optional[SubCategory]:
        return self.session.query(self.model).filter(
            self.model.name == name,
            self.model.place_id == place_id,
            self.model.is_deleted == False
        ).first()
