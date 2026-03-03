from typing import List
from sqlalchemy.orm import Session

from src.models.item import Item
from src.models.place import Place
from src.schemas.item import ItemCreate, ItemUpdate
from src.repositories.item_repository import ItemRepository
from src.core.permissions import require_place_owner_or_admin

class ItemService:
    def __init__(self, session: Session):
        self.repo = ItemRepository(session)

    def create_item(self, place_id: int, item_in: ItemCreate, current_user) -> Item:
        # get place
        place = self.repo.session.query(Place).filter(Place.id == place_id).first()
        if not place:
            raise ValueError("Place not found")

        # permission check: Only place owner or admin can create items
        require_place_owner_or_admin(current_user, place)

        item = Item(**item_in.model_dump(), place_id=place_id)
        return self.repo.create(item)

    def get_items_by_place(self, place_id: int, skip: int = 0, limit: int = 100) -> List[Item]:
        return self.repo.get_by_place(place_id, skip, limit)

    def update_item(self, item_id: int, item_in: ItemUpdate, current_user) -> Item:
        db_item = self.repo.session.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            raise ValueError("Item not found")

        place = db_item.place
        require_place_owner_or_admin(current_user, place)

        update_data = item_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)

        self.repo.session.flush()
        return db_item

    def delete_item(self, item_id: int, current_user) -> Item:
        db_item = self.repo.session.query(Item).filter(Item.id == item_id).first()
        if not db_item:
            raise ValueError("Item not found")

        place = db_item.place
        require_place_owner_or_admin(current_user, place)

        db_item.is_active = False
        self.repo.session.flush()
        return db_item