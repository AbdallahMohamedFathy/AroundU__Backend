from typing import List
from sqlalchemy.orm import Session

from src.models.item import Item
from src.schemas.item import ItemCreate, ItemUpdate
from src.repositories.item_repository import ItemRepository
from src.core.dependencies import get_current_user
from src.core.security import is_admin_or_owner

class ItemService:
    def __init__(self, session: Session):
        self.repo = ItemRepository(session)

    def create_item(self, place_id: int, item_in: ItemCreate, current_user) -> Item:
        # Verify ownership or admin
        if not is_admin_or_owner(current_user, place_id, session=self.repo.session):
            raise PermissionError("Not authorized to create items for this place")
        item = Item(**item_in.model_dump(), place_id=place_id)
        return self.repo.create(item)

    def get_items_by_place(self, place_id: int, skip: int = 0, limit: int = 100) -> List[Item]:
        return self.repo.get_by_place(place_id, skip, limit)

    def update_item(self, item_id: int, item_in: ItemUpdate, current_user) -> Item:
        db_item = self.repo.session.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            raise ValueError("Item not found")
        if not is_admin_or_owner(current_user, db_item.place_id, session=self.repo.session):
            raise PermissionError("Not authorized to update this item")
        update_data = item_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        self.repo.session.flush()
        return db_item

    def delete_item(self, item_id: int, current_user) -> Item:
        db_item = self.repo.session.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            raise ValueError("Item not found")
        if not is_admin_or_owner(current_user, db_item.place_id, session=self.repo.session):
            raise PermissionError("Not authorized to delete this item")
        # Soft delete by deactivating
        db_item.is_active = False
        self.repo.session.flush()
        return db_item
