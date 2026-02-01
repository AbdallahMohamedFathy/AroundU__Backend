from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from src.core.database import get_db
from src.schemas.place import PlaceResponse
from src.api.v1.auth import get_current_user
from src.models.user import User
from src.services.search_service import search_places, get_recent_searches, get_trending_searches

router = APIRouter()

@router.get("/", response_model=List[PlaceResponse])
def search(
    q: Optional[str] = None, 
    category: Optional[str] = None, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user) # Optional auth for tracking
):
    user_id = current_user.id if current_user else None
    return search_places(db, query=q, category=category, user_id=user_id)

@router.get("/recent", response_model=List[str])
def recent_searches(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_recent_searches(db, user_id=current_user.id)

@router.get("/trending")
def trending_searches_api(db: Session = Depends(get_db)):
    return get_trending_searches(db)
