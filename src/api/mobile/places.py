from fastapi import APIRouter, Depends, Query, BackgroundTasks
from typing import Optional, List
from src.core.dependencies import get_place_repository, get_uow, get_place_image_repository, get_current_user_optional
from src.schemas.place import PlaceResponse, PlaceListResponse, NearbyPlaceListResponse, NearbyPlaceResponse
from src.models.user import User
from src.services.place_service import (
    get_places, get_place_by_id, get_nearby_places, get_trending_places
)
from src.models.interaction import Interaction
from src.services import place_image_service
from src.schemas.place_image import PlaceImageResponse
from src.core.logger import logger
from src.services.ai_location_service import ai_location_service

router = APIRouter()

# ─── Helper for background visits ───
async def record_view_visit(
    place_id: int, 
    uow, 
    user_id: Optional[int] = None, 
    lat: Optional[float] = None, 
    lon: Optional[float] = None
):
    cluster_id: Optional[int] = None
    if lat is not None and lon is not None:
        try:
            cluster_data = await ai_location_service.predict_cluster(lat, lon)
            print("AI RESPONSE (View):", cluster_data)
            if cluster_data and "cluster" in cluster_data:
                cluster_id = int(cluster_data["cluster"])
            else:
                logger.warning("[record_view_visit] Invalid cluster response")
        except Exception as exc:
            logger.warning(f"[record_view_visit] Cluster prediction failed: {exc}")

    with uow:
        visit = Interaction(
            place_id=place_id, 
            user_id=user_id,
            user_lat=lat,
            user_lon=lon,
            cluster_id=cluster_id,
            type="visit"
        )
        uow.interaction_repository.create(visit)
        uow.commit()


# ─── LIST  GET /places ───────────────────────────────────────────────────────
@router.get("/", response_model=PlaceListResponse)
def list_places(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    sort_by: str = Query("created_at", description="created_at | rating | name | review_count"),
    sort_order: str = Query("desc", description="asc or desc"),
    repo = Depends(get_place_repository),
    uow = Depends(get_uow),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Return a paginated list of all active places."""
    result = get_places(repo, page=page, page_size=page_size,
                      category_id=category_id, sort_by=sort_by, sort_order=sort_order)
    
    if current_user:
        with uow:
            fav_place_ids = uow.favorite_repository.get_user_favorite_place_ids(current_user.id)
        new_items = []
        for item in result["items"]:
            response_item = PlaceResponse.model_validate(item)
            response_item.is_favorited = response_item.id in fav_place_ids
            new_items.append(response_item)
        result["items"] = new_items
    else:
        result["items"] = [PlaceResponse.model_validate(item) for item in result["items"]]
        
    return result


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
    uow = Depends(get_uow),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Return places sorted by distance from the supplied coordinates."""
    result = get_nearby_places(repo, latitude, longitude, radius_km,
                             category_id=category_id, page=page, page_size=page_size)
    
    if current_user:
        with uow:
            fav_place_ids = uow.favorite_repository.get_user_favorite_place_ids(current_user.id)
        new_items = []
        for item in result["items"]:
            response_item = NearbyPlaceResponse.model_validate(item)
            response_item.is_favorited = response_item.id in fav_place_ids
            new_items.append(response_item)
        result["items"] = new_items
    else:
        result["items"] = [NearbyPlaceResponse.model_validate(item) for item in result["items"]]
        
    return result


# ─── TRENDING  GET /places/trending ─────────────────────────────────────────
@router.get("/trending", response_model=PlaceListResponse)
def trending_places(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    category_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    repo = Depends(get_place_repository),
    uow = Depends(get_uow),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Return places ranked by a trending score (Rating + Favorites + Distance)."""
    result = get_trending_places(
        repo, latitude, longitude, 
        category_id=category_id, page=page, page_size=page_size
    )
    
    if current_user:
        with uow:
            fav_place_ids = uow.favorite_repository.get_user_favorite_place_ids(current_user.id)
        new_items = []
        for item in result["items"]:
            # item is a dict from repo.get_trending
            response_item = PlaceResponse.model_validate(item)
            response_item.is_favorited = response_item.id in fav_place_ids
            new_items.append(response_item)
        result["items"] = new_items
    else:
        result["items"] = [PlaceResponse.model_validate(item) for item in result["items"]]
        
    return result


# ─── GET ONE  GET /places/{id} ──────────────────────────────────────────────
@router.get("/{place_id}", response_model=PlaceResponse)
def get_place(
    place_id: int, 
    background_tasks: BackgroundTasks,
    user_lat: Optional[float] = Query(None, ge=-90, le=90),
    user_lon: Optional[float] = Query(None, ge=-180, le=180),
    repo = Depends(get_place_repository),
    uow = Depends(get_uow),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Retrieve a single place by ID and record a visit in the background."""
    place = get_place_by_id(repo, place_id)
    background_tasks.add_task(
        record_view_visit, 
        place_id, 
        uow, 
        current_user.id if current_user else None,
        user_lat,
        user_lon
    )
    
    response_data = PlaceResponse.model_validate(place)
    if current_user:
        with uow:
            fav = uow.favorite_repository.get_by_user_and_place(current_user.id, place_id)
            response_data.is_favorited = fav is not None
            
    return response_data

@router.get("/{place_id}/images", response_model=List[PlaceImageResponse])
def list_place_images(
    place_id: int, 
    repo = Depends(get_place_image_repository)
):
    """Retrieve all images (place and menu) for a specific place."""
    return place_image_service.get_place_images(repo, place_id)
