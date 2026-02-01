from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.core.database import get_db
from src.schemas.place import PlaceResponse, PlaceBase
from src.services.place_service import get_places, create_place, get_places_by_category

router = APIRouter()

@router.get("/", response_model=List[PlaceResponse])
def read_places(skip: int = 0, limit: int = 100, category_id: int = None, db: Session = Depends(get_db)):
    if category_id:
        return get_places_by_category(db, category_id)
    return get_places(db, skip=skip, limit=limit)

@router.post("/", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
def create_new_place(place: PlaceBase, db: Session = Depends(get_db)):
    return create_place(db, place)
