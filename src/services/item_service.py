from typing import List, Any
from src.core.unit_of_work import UnitOfWork
from src.models.item import Item
from src.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from src.core.permissions import require_place_owner_or_admin
from src.core.exceptions import APIException
from fastapi import status

def get_items_by_place(repo: Any, place_id: int, skip: int = 0, limit: int = 100):
    """Return all items for a given place."""
    return repo.get_by_place(place_id, skip, limit)

def create_item(uow: UnitOfWork, place_id: int, item_in: ItemCreate, current_user: Any):
    """Create a new item if user is place owner or admin."""
    with uow:
        # Fetch place to check ownership
        place = uow.place_repository.get_by_id(place_id)
        if not place:
            raise APIException("Place not found", code=status.HTTP_404_NOT_FOUND)
        
        # Enforce Ownership
        require_place_owner_or_admin(current_user, place)
        
        db_item = Item(**item_in.model_dump(), place_id=place_id)
        uow.item_repository.create(db_item)
        uow.commit()
        return ItemResponse.model_validate(db_item)

def update_item(uow: UnitOfWork, item_id: int, item_in: ItemUpdate, current_user: Any):
    """Update item if user is place owner or admin."""
    with uow:
        db_item = uow.item_repository.get_by_id(item_id)
        if not db_item:
            raise APIException("Item not found", code=status.HTTP_404_NOT_FOUND)
            
        place = db_item.place
        require_place_owner_or_admin(current_user, place)
        
        uow.item_repository.update(db_item, item_in)
        uow.commit()
        return ItemResponse.model_validate(db_item)

def delete_item(uow: UnitOfWork, item_id: int, current_user: Any):
    """Delete (deactivate) item if user is place owner or admin."""
    with uow:
        db_item = uow.item_repository.get_by_id(item_id)
        if not db_item:
            raise APIException("Item not found", code=status.HTTP_404_NOT_FOUND)
            
        place = db_item.place
        require_place_owner_or_admin(current_user, place)
        
        uow.item_repository.delete(db_item)
        uow.commit()
        return True