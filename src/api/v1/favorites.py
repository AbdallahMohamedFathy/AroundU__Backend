from fastapi import APIRouter, Depends, status
from typing import List
from src.core.dependencies import get_favorite_repository, get_uow
from src.api.v1.auth import get_current_user
from src.models.user import User
from src.schemas.favorite import FavoriteCreate, FavoriteResponse
from src.services import favorite_service

router = APIRouter()


# ─── LIST  GET /favorites ────────────────────────────────────────────────────
@router.get("/", response_model=List[FavoriteResponse])
def list_favorites(
    repo=Depends(get_favorite_repository),
    current_user: User = Depends(get_current_user),
):
    """Return all places the current user has favorited."""
    return favorite_service.get_user_favorites(repo, current_user.id)


# ─── ADD  POST /favorites ────────────────────────────────────────────────────
@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
def add_to_favorites(
    data: FavoriteCreate,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Add a place to the current user's favorites."""
    return favorite_service.add_favorite(uow, current_user.id, data)


# ─── REMOVE  DELETE /favorites/{place_id} ───────────────────────────────────
@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_favorites(
    place_id: int,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Remove a place from the current user's favorites."""
    favorite_service.remove_favorite(uow, current_user.id, place_id)
