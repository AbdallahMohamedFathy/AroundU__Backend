from fastapi import APIRouter, Depends, Query
from typing import Optional
from src.core.dependencies import get_place_repository
from src.schemas.place import PlaceResponse, PlaceListResponse, NearbyPlaceListResponse
from src.services.place_service import (
    get_places, get_place_by_id, get_nearby_places,
)
from src.services import place_image_service
from src.schemas.place_image import PlaceImageResponse
from src.core.dependencies import get_place_image_repository
from typing import List

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

@router.get("/{place_id}/images", response_model=List[PlaceImageResponse])
def list_place_images(
    place_id: int, 
    repo = Depends(get_place_image_repository)
):
    """Retrieve all images (place and menu) for a specific place."""
    return place_image_service.get_place_images(repo, place_id)
