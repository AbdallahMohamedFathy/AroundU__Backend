from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.schemas.item import ItemResponse
from src.services.item_service import ItemService

router = APIRouter()

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
