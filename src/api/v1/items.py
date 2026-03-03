from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from src.services.item_service import ItemService
from src.models.user import User

router = APIRouter()

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    place_id: int,
    item_in: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new item for a specific place.
    Only the place owner or an admin can perform this action.
    """
    service = ItemService(db)
    return service.create_item(place_id=place_id, item_in=item_in, current_user=current_user)


@router.get("/place/{place_id}", response_model=List[ItemResponse])
def list_place_items(
    place_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all items for a specific place.
    """
    service = ItemService(db)
    return service.get_items_by_place(place_id=place_id, skip=skip, limit=limit)


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item_in: ItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing item.
    Only the place owner or an admin can perform this action.
    """
    service = ItemService(db)
    return service.update_item(item_id=item_id, item_in=item_in, current_user=current_user)


@router.delete("/{item_id}", response_model=ItemResponse)
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an item (soft delete).
    Only the place owner or an admin can perform this action.
    """
    service = ItemService(db)
    return service.delete_item(item_id=item_id, current_user=current_user)
