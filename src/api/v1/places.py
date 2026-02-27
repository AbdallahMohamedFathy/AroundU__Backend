from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from src.core.dependencies import get_place_repository, get_uow
from src.api.v1.auth import get_current_user
from src.models.user import User
from src.schemas.place import PlaceCreate, PlaceUpdate, PlaceResponse, PlaceListResponse
from src.services.place_service import (
    get_places, get_place_by_id, get_nearby_places,
    create_place, update_place, delete_place,
)

router = APIRouter()


# ─── LIST  GET /places ───────────────────────────────────────────────────────
@router.get("/", response_model=PlaceListResponse)
def list_places(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    sort_by: str = Query("created_at", description="created_at | rating | name | review_count"),
    sort_order: str = Query("desc", description="asc or desc"),
    repo = Depends(get_place_repository),
):
    """Return a paginated list of all active places."""
    return get_places(repo, page=page, page_size=page_size,
                      category_id=category_id, sort_by=sort_by, sort_order=sort_order)


# ─── NEARBY  GET /places/nearby ─────────────────────────────────────────────
from src.schemas.place import NearbyPlaceListResponse
@router.get("/nearby", response_model=NearbyPlaceListResponse)
def nearby_places(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(5.0, ge=0.1, le=50),
    category_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repo = Depends(get_place_repository),
):
    """Return places sorted by distance from the supplied coordinates."""
    return get_nearby_places(repo, latitude, longitude, radius_km,
                             category_id=category_id, page=page, page_size=page_size)


# ─── GET ONE  GET /places/{id} ──────────────────────────────────────────────
@router.get("/{place_id}", response_model=PlaceResponse)
def get_place(place_id: int, repo = Depends(get_place_repository)):
    """Retrieve a single place by ID."""
    return get_place_by_id(repo, place_id)


# ─── CREATE  POST /places ───────────────────────────────────────────────────
@router.post("/", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
def create_new_place(
    place: PlaceCreate,
    uow = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Create a new place. Requires authentication."""
    return create_place(uow, place)


# ─── UPDATE  PUT /places/{id} ───────────────────────────────────────────────
@router.put("/{place_id}", response_model=PlaceResponse)
def update_existing_place(
    place_id: int,
    place_data: PlaceUpdate,
    uow = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Partially update a place. Requires authentication."""
    return update_place(uow, place_id, place_data)


# ─── DELETE  DELETE /places/{id} ────────────────────────────────────────────
@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_place(
    place_id: int,
    uow = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Hard-delete a place. Requires authentication."""
    delete_place(uow, place_id)
