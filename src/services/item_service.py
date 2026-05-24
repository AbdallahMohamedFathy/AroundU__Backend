from typing import List, Optional, Any, Tuple
from src.core.unit_of_work import UnitOfWork
from src.models.item import Item
from src.schemas.item import ItemCreate, ItemUpdate
from src.core.exceptions import APIException
from fastapi import status
import datetime

def get_items(repo: Any, name: Optional[str] = None, sub_category_id: Optional[int] = None, place_id: Optional[int] = None, skip: int = 0, limit: int = 10):
    return repo.search_items(name=name, sub_category_id=sub_category_id, place_id=place_id, skip=skip, limit=limit)

def get_items_by_subcategory(repo: Any, sub_category_id: int):
    return repo.get_by_subcategory(sub_category_id)

def get_items_by_place(repo: Any, place_id: int):
    return repo.get_by_place(place_id)

def get_top_items_by_place(repo: Any, place_id: int, limit: int = 4):
    return repo.get_top_by_place(place_id=place_id, limit=limit)

def create_item(uow: UnitOfWork, item_in: ItemCreate, user_id: int, user_role: str = "OWNER"):
    with uow:
        # 1. Determine sub_category_id
        target_sub_id = item_in.sub_category_id
        
        if not target_sub_id:
            if not item_in.place_id:
                raise APIException("Either sub_category_id or place_id is required", code=status.HTTP_400_BAD_REQUEST)
            
            # Find first subcategory for this place
            existing_subs = uow.subcategory_repository.get_by_place(item_in.place_id)
            if existing_subs:
                target_sub_id = existing_subs[0].id
            else:
                # Create a default subcategory
                from src.models.subcategory import SubCategory
                default_sub = SubCategory(
                    name="General",
                    place_id=item_in.place_id,
                    owner_id=user_id
                )
                uow.subcategory_repository.create(default_sub)
                uow.session.flush()
                target_sub_id = default_sub.id

        # 2. Check if subcategory exists and belongs to owner
        subcategory = uow.subcategory_repository.get_by_id(target_sub_id)
        if not subcategory or subcategory.is_deleted:
            raise APIException("SubCategory not found", code=status.HTTP_404_NOT_FOUND)
        
        if user_role != "ADMIN" and subcategory.owner_id != user_id:
            raise APIException("You don't have permission to add items to this branch", code=status.HTTP_403_FORBIDDEN)

        # Prevent duplicate item names inside same subcategory
        existing = uow.item_repository.get_by_name_and_subcategory(item_in.name, target_sub_id)
        if existing:
            raise APIException("Item with this name already exists in this subcategory", code=status.HTTP_400_BAD_REQUEST)

        # 3. Create Item
        # Remove place_id from dict as it's not a model field
        item_data = item_in.model_dump()
        item_data.pop("place_id", None)
        item_data["sub_category_id"] = target_sub_id
        
        db_item = Item(**item_data)
        uow.item_repository.create(db_item)
        uow.commit()
        return uow.item_repository.get_by_id(db_item.id)

def update_item(uow: UnitOfWork, item_id: int, item_in: ItemUpdate, user_id: int, user_role: str = "OWNER"):
    with uow:
        db_item = uow.item_repository.get_by_id(item_id)
        if not db_item or db_item.is_deleted:
            raise APIException("Item not found", code=status.HTTP_404_NOT_FOUND)
            
        # Check ownership via subcategory
        subcategory = uow.subcategory_repository.get_by_id(db_item.sub_category_id)
        if not subcategory:
            raise APIException("SubCategory not found", code=status.HTTP_404_NOT_FOUND)
        if user_role != "ADMIN" and subcategory.owner_id != user_id:
            raise APIException("You don't have permission to update this item", code=status.HTTP_403_FORBIDDEN)

        if item_in.name and item_in.name != db_item.name:
            target_sub_id = item_in.sub_category_id or db_item.sub_category_id
            existing = uow.item_repository.get_by_name_and_subcategory(item_in.name, target_sub_id)
            if existing:
                raise APIException("Item with this name already exists in this subcategory", code=status.HTTP_400_BAD_REQUEST)

        update_data = item_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        uow.session.flush()
        uow.session.refresh(db_item)
        uow.commit()
        return uow.item_repository.get_by_id(db_item.id)

def delete_item(uow: UnitOfWork, item_id: int, user_id: int, user_role: str = "OWNER"):
    with uow:
        db_item = uow.item_repository.get_by_id(item_id)
        if not db_item or db_item.is_deleted:
            raise APIException("Item not found", code=status.HTTP_404_NOT_FOUND)
            
        subcategory = uow.subcategory_repository.get_by_id(db_item.sub_category_id)
        if user_role != "ADMIN" and subcategory.owner_id != user_id:
            raise APIException("You don't have permission to delete this item", code=status.HTTP_403_FORBIDDEN)

        # Soft delete
        db_item.is_deleted = True
        db_item.deleted_at = datetime.datetime.now(datetime.timezone.utc)
        uow.commit()
        return True

def toggle_availability(uow: UnitOfWork, item_id: int, user_id: int, user_role: str = "OWNER"):
    with uow:
        db_item = uow.item_repository.get_by_id(item_id)
        if not db_item or db_item.is_deleted:
            raise APIException("Item not found", code=status.HTTP_404_NOT_FOUND)
            
        subcategory = uow.subcategory_repository.get_by_id(db_item.sub_category_id)
        if user_role != "ADMIN" and subcategory.owner_id != user_id:
            raise APIException("You don't have permission to modify this item", code=status.HTTP_403_FORBIDDEN)

        db_item.is_available = not db_item.is_available
        uow.commit()
        return uow.item_repository.get_by_id(db_item.id)

def update_item_image(uow: UnitOfWork, item_id: int, image_url: str, user_id: int, user_role: str = "OWNER"):
    with uow:
        db_item = uow.item_repository.get_by_id(item_id)
        if not db_item or db_item.is_deleted:
            raise APIException("Item not found", code=status.HTTP_404_NOT_FOUND)
            
        subcategory = uow.subcategory_repository.get_by_id(db_item.sub_category_id)
        if user_role != "ADMIN" and subcategory.owner_id != user_id:
            raise APIException("You don't have permission to update this item", code=status.HTTP_403_FORBIDDEN)

        db_item.image_url = image_url
        uow.commit()
        return uow.item_repository.get_by_id(db_item.id)