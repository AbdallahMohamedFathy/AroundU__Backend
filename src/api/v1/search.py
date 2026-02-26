from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional
from src.core.dependencies import get_search_repository, get_uow
from src.schemas.place import PlaceResponse
from src.api.v1.auth import get_current_user
from src.models.user import User
from src.services import search_service

router = APIRouter()

@router.get("/", response_model=List[PlaceResponse])
def search(
    q: Optional[str] = None, 
    category: Optional[str] = None, 
    uow=Depends(get_uow),
    current_user: Optional[User] = Depends(get_current_user)
):
    user_id = current_user.id if current_user else None
    return search_service.search_places(uow, query=q, category=category, user_id=user_id)

@router.get("/recent", response_model=List[str])
def recent_searches(repo=Depends(get_search_repository), current_user: User = Depends(get_current_user)):
    return search_service.get_recent_searches(repo, user_id=current_user.id)

@router.get("/trending")
def trending_searches_api(repo=Depends(get_search_repository)):
    return search_service.get_trending_searches(repo)
