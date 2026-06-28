"""
owner.py  (Dashboard API)
--------------------------
Owner and Admin dashboard endpoints for AroundU.

Anomaly detection strategy
---------------------------
All anomaly calls here are BATCH — they run when the dashboard loads and
operate over historical data. Real-time detection (per-request) lives in
interactions.py.

  GET /api/owner/anomalies           → place anomalies for the current owner
  GET /api/owner/anomalies/summary   → metrics summary for current owner's place
  GET /api/owner/location-heatmap    → AI heatmap for owner's visit data
  GET /api/owner/opportunities       → AI business opportunities
  GET /api/admin/anomalies/summary   → district-wide summary across ALL places
"""

from __future__ import annotations

import traceback
from datetime import date, datetime, timedelta
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from src.api.dashboard.dependencies import owner_guard
from src.core.dependencies import get_db, get_uow, get_place_image_repository, get_review_repository, get_item_repository
from src.core.exceptions import APIException
from src.core.logger import logger
from src.models.favorite import Favorite
from src.models.interaction import Interaction
from src.models.place import Place
from src.models.review import Review
from src.models.user import User
try:
    from app.orders.models.order_models import Order
except ImportError:
    Order = None
from src.schemas.item import ItemResponse
from src.schemas.place import PlaceResponse, PlaceUpdate
from src.schemas.place_image import PlaceImageCreate, PlaceImageResponse
from src.schemas.review import ReviewListResponse
from src.services import place_image_service, review_service, item_service
from src.services.ai_service import ai_connector
from src.services.anomaly_helpers import (
    prepare_district_data,
    prepare_place_anomaly_payload,
    prepare_place_metrics,
    prepare_user_visits,
)

router = APIRouter(dependencies=[Depends(owner_guard)])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_target_place_id(db: Session, owner_id: int, place_id: Optional[int] = None) -> int:
    """Helper to get the target place_id for dashboard operations with security check."""
    # 1. Try provided ID
    if place_id:
        place = db.query(Place).filter(Place.id == place_id, Place.owner_id == owner_id).first()
        if place:
            return place.id
    
    # 2. Try default (first) place
    place = db.query(Place).filter(Place.owner_id == owner_id).order_by(Place.id.asc()).first()
    if not place:
        raise APIException("No place found for this owner", code=status.HTTP_404_NOT_FOUND)
    
    return place.id


# ---------------------------------------------------------------------------
# My Place
# ---------------------------------------------------------------------------

@router.get("/my-place", response_model=PlaceResponse)
def get_my_place(
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Return the current owner's primary (first) place details."""
    try:
        place = db.query(Place).filter(Place.owner_id == current_user.id).order_by(Place.id.asc()).first()
        if not place:
            raise APIException(
                "No place found for this owner", code=status.HTTP_404_NOT_FOUND
            )
        return PlaceResponse.model_validate(place)
    except APIException:
        raise
    except Exception:
        logger.error(f"Error in get_my_place: {traceback.format_exc()}")
        raise APIException("Internal error fetching place", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/my-places", response_model=List[PlaceResponse])
def get_my_places(
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Return all places owned by the current owner."""
    places = db.query(Place).filter(Place.owner_id == current_user.id).order_by(Place.id.asc()).all()
    return [PlaceResponse.model_validate(p) for p in places]

@router.post("/add-branch", response_model=PlaceResponse)
def add_branch(
    branch_data: Dict[str, Any], # payload: {"location_link": "...", "latitude": 0.0, ...}
    uow: Annotated[Any, Depends(get_uow)],
    current_user=Depends(owner_guard),
):
    """Create a new branch by copying data from the owner's primary place."""
    from src.utils.location_parser import extract_coordinates
    
    with uow:
        try:
            # 1. Get primary place to copy from
            primary_place = uow.place_repository.get_by_owner_id(current_user.id)
            if not primary_place:
                raise APIException("You must have a primary place before adding branches", code=status.HTTP_400_BAD_REQUEST)
            
            # 2. Extract coordinates (prefer pre-extracted from dashboard)
            lat = branch_data.get("latitude")
            lng = branch_data.get("longitude")
            
            if lat is None or lng is None:
                loc_link = branch_data.get("location_link")
                if not loc_link:
                    raise APIException("Google Maps link or coordinates are required", code=status.HTTP_400_BAD_REQUEST)
                    
                coords = extract_coordinates(loc_link)
                if not coords:
                    raise APIException("Could not parse location link", code=status.HTTP_400_BAD_REQUEST)
                lat, lng = coords
            
            address = branch_data.get("address") or primary_place.address

            # 3. Create new place record
            new_branch = Place(
                name=primary_place.name,
                description=primary_place.description,
                address=address,
                phone=primary_place.phone,
                website=primary_place.website,
                category_id=primary_place.category_id,
                owner_id=current_user.id,
                parent_id=primary_place.id,  # Establishment of hierarchy
                latitude=float(lat),
                longitude=float(lng),
                facebook_url=primary_place.facebook_url,
                instagram_url=primary_place.instagram_url,
                whatsapp_number=primary_place.whatsapp_number,
                tiktok_url=primary_place.tiktok_url,
                is_active=True
            )
            
            new_branch = uow.place_repository.create(new_branch)
            
            # 4. Set PostGIS location
            uow.session.execute(
                text("""
                    UPDATE places
                    SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                    WHERE id = :id
                """),
                {"lng": float(lng), "lat": float(lat), "id": new_branch.id}
            )
            
            # 5. Copy images
            from src.models.place_image import PlaceImage
            for img in primary_place.images:
                new_img = PlaceImage(
                    place_id=new_branch.id,
                    image_url=img.image_url,
                    image_type=img.image_type,
                    caption=getattr(img, 'caption', None) # Safe access
                )
                uow.session.add(new_img)
                
            uow.commit()
            return PlaceResponse.model_validate(new_branch)
        except Exception as e:
            uow.rollback()
            raise APIException(f"Failed to copy data: {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.delete("/branches/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_branch(
    branch_id: int,
    uow: Annotated[Any, Depends(get_uow)],
    current_user=Depends(owner_guard),
):
    """Delete a specific branch belonging to the owner."""
    with uow:
        branch = uow.place_repository.get_by_id(branch_id)
        
        if not branch:
            raise APIException("Branch not found", code=status.HTTP_404_NOT_FOUND)
            
        # Security: Must be the owner
        if branch.owner_id != current_user.id:
            raise APIException("Not authorized to delete this place", code=status.HTTP_403_FORBIDDEN)
            
        # Business Logic: Only branches (places with parents) can be deleted via this endpoint
        if branch.parent_id is None:
            raise APIException("Primary establishment cannot be deleted via branch endpoint", code=status.HTTP_400_BAD_REQUEST)
            
        uow.place_repository.delete(branch)
        uow.commit()
        return None


@router.patch("/branches/{branch_id}", response_model=PlaceResponse)
def update_branch(
    branch_id: int,
    payload: PlaceUpdate,
    uow: Annotated[Any, Depends(get_uow)],
    current_user=Depends(owner_guard),
):
    """Update any field of a specific branch belonging to the owner."""
    with uow:
        branch = uow.place_repository.get_by_id(branch_id)
        
        if not branch:
            raise APIException("Branch not found", code=status.HTTP_404_NOT_FOUND)
            
        # Security: Must be the owner
        if branch.owner_id != current_user.id:
            raise APIException("Not authorized to update this place", code=status.HTTP_403_FORBIDDEN)
            
        # Update fields
        update_data = payload.model_dump(exclude_unset=True)
        
        # Special handling for coordinates to update PostGIS location
        lat = update_data.get("latitude")
        lng = update_data.get("longitude")
        
        updated_branch = uow.place_repository.update(branch, update_data)
        
        if lat is not None or lng is not None:
            new_lat = lat if lat is not None else branch.latitude
            new_lng = lng if lng is not None else branch.longitude
            uow.session.execute(
                text("""
                    UPDATE places
                    SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                    WHERE id = :id
                """),
                {"lng": float(new_lng), "lat": float(new_lat), "id": branch.id}
            )
            
        uow.commit()
        return PlaceResponse.model_validate(updated_branch)
@router.get("/customers")
def get_owner_customers(
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Get a list of unique users who have placed orders at the owner's places."""
    from app.orders.models.order_models import Order
    from src.models.user import User
    
    # 1. Get all place IDs owned by this user
    place_ids = [p.id for p in db.query(Place.id).filter(Place.owner_id == current_user.id).all()]
    
    # 2. Find unique user IDs from orders at these places
    user_ids = db.query(Order.user_id).filter(Order.place_id.in_(place_ids)).distinct().all()
    user_ids = [u[0] for u in user_ids]
    
    # 3. Fetch user details
    customers = db.query(User).filter(User.id.in_(user_ids)).all()
    
    return [
        {"id": c.id, "name": c.full_name or c.email, "email": c.email}
        for c in customers
    ]


# ---------------------------------------------------------------------------
# Dashboard KPIs
# ---------------------------------------------------------------------------

@router.get("/dashboard")
@router.get("/{place_id:int}")
def get_owner_dashboard(
    place_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Get high-level KPI metrics from real interactions."""
    try:
        # 1. Determine target place_id
        target_place_id = resolve_target_place_id(db, current_user.id, place_id)
        
        logger.info(f"Dashboard Request - Place: {target_place_id}")

        # 3. Query Interactions (Visits, Calls, Directions)
        query = db.query(Interaction.type, func.count(Interaction.id)).filter(
            Interaction.place_id == target_place_id
        )
        results = query.group_by(Interaction.type).all()

        # 4. Query Favorites (Saves)
        fav_query = db.query(func.count(Favorite.id)).filter(
            Favorite.place_id == target_place_id
        )
        favorite_count = fav_query.scalar() or 0
        
        # 5. Query Actual Orders
        order_count = 0
        if Order:
            order_query = db.query(func.count(Order.id)).filter(
                Order.place_id == target_place_id
            )
            order_count = order_query.scalar() or 0

        stats = {
            "visits": 0,
            "orders": order_count,
            "saves": favorite_count,
            "calls": 0,
            "directions": 0,
        }
        for type_, count in results:
            if type_ == "visit":
                stats["visits"] = count
            elif type_ == "call":
                stats["calls"] = count
            elif type_ == "direction":
                stats["directions"] = count
            elif type_ == "order" and order_count == 0:
                stats["orders"] = count

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_owner_dashboard: {traceback.format_exc()}")
        raise APIException(f"Dashboard failed: {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/places/{place_id}/reviews", response_model=ReviewListResponse)
def get_owner_place_reviews(
    place_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    repo=Depends(get_review_repository),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Owner: Get reviews for a specific branch."""
    # Verify ownership
    place = db.query(Place).filter(Place.id == place_id, Place.owner_id == current_user.id).first()
    if not place:
        raise APIException("Place not found or access denied", code=status.HTTP_404_NOT_FOUND)

    return review_service.get_place_reviews(repo, place_id, page, page_size)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner_review(
    review_id: int,
    uow=Depends(get_uow),
    current_user=Depends(owner_guard),
):
    """Owner: Delete a review left on any of their places."""
    review_service.delete_review(uow, review_id, current_user)
    return None

# ─── PROPERTY REVIEWS (Owner Dashboard) ─────────────────────────────────────
@router.get("/properties/{property_id}/reviews")
def get_owner_property_reviews(
    property_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Owner: Get reviews for one of their property listings."""
    from src.models.property import Property
    from src.repositories.property_repository import PropertyRepository
    from src.services import property_service as prop_svc

    prop = db.query(Property).filter(Property.id == property_id, Property.owner_id == current_user.id).first()
    if not prop:
        raise APIException("Property not found or access denied", code=status.HTTP_404_NOT_FOUND)

    repo = PropertyRepository(db)
    return prop_svc.get_property_reviews(repo, property_id, page, page_size)


@router.delete("/properties/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_owner_property_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Owner: Delete a review left on any of their property listings."""
    from src.repositories.property_repository import PropertyRepository
    from src.services import property_service as prop_svc

    repo = PropertyRepository(db)
    prop_svc.delete_property_review(repo, review_id, current_user)
    return None

@router.get("/places/{place_id}/items", response_model=List[ItemResponse])
def get_owner_place_items(
    place_id: int,
    repo=Depends(get_item_repository),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Owner: Get all items for a specific branch."""
    # Verify ownership
    place = db.query(Place).filter(Place.id == place_id, Place.owner_id == current_user.id).first()
    if not place:
        raise APIException("Place not found or access denied", code=status.HTTP_404_NOT_FOUND)
        
    return item_service.get_items_by_place(repo, place_id)


# ---------------------------------------------------------------------------
# Analytics time-series
# ---------------------------------------------------------------------------

@router.get("/analytics")
def get_owner_analytics(
    place_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Get real time-series analytics data grouped by day."""
    try:
        target_place_id = resolve_target_place_id(db, current_user.id, place_id)

        t_date = datetime.now().date()
        f_date = (datetime.now() - timedelta(days=30)).date()

        results = (
            db.query(
                func.date(Interaction.created_at).label("day"),
                Interaction.type,
                func.count(Interaction.id).label("count"),
            )
            .filter(
                Interaction.place_id == target_place_id,
                func.date(Interaction.created_at) >= f_date,
                func.date(Interaction.created_at) <= t_date,
            )
            .group_by(func.date(Interaction.created_at), Interaction.type)
            .all()
        )

        daily_data: Dict[str, Dict] = {}
        curr = f_date
        while curr <= t_date:
            d_str = curr.strftime("%Y-%m-%d")
            daily_data[d_str] = {
                "date": d_str,
                "visits": 0,
                "orders": 0,
                "saves": 0,
                "directions": 0,
                "calls": 0,
            }
            curr += timedelta(days=1)

        # 3. Query Interactions
        query = db.query(
            func.date(Interaction.created_at).label("day"),
            Interaction.type,
            func.count(Interaction.id).label("count"),
        ).filter(
            Interaction.place_id == target_place_id
        ).group_by(
            func.date(Interaction.created_at),
            Interaction.type
        )
        results = query.all()

        # 4. Query Favorites
        fav_results = (
            db.query(
                func.date(Favorite.created_at).label("day"),
                func.count(Favorite.id).label("count"),
            )
            .filter(
                Favorite.place_id == target_place_id
            )
            .group_by(func.date(Favorite.created_at))
            .all()
        )

        for day, type_, count in results:
            d_str = day.strftime("%Y-%m-%d")
            if d_str not in daily_data or type_ == "save":
                continue
            key = {
                "visit": "visits",
                "order": "orders",
                "call": "calls",
                "direction": "directions",
            }.get(type_)
            if key:
                daily_data[d_str][key] = count

        for day, count in fav_results:
            d_str = day.strftime("%Y-%m-%d")
            if d_str in daily_data:
                daily_data[d_str]["saves"] = count

        if Order:
            order_results = (
                db.query(
                    func.date(Order.created_at).label("day"),
                    func.count(Order.id).label("count"),
                )
                .filter(
                    Order.place_id == target_place_id
                )
                .group_by(func.date(Order.created_at))
                .all()
            )
            for day, count in order_results:
                d_str = day.strftime("%Y-%m-%d")
                if d_str in daily_data:
                    daily_data[d_str]["orders"] = count

        return sorted(daily_data.values(), key=lambda x: x["date"])

    except HTTPException:
        raise
    except Exception:
        logger.error(f"Error in get_owner_analytics: {traceback.format_exc()}")
        raise APIException("Analytics failed", code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# Chatbot stats
# ---------------------------------------------------------------------------

@router.get("/chatbot-stats")
def get_chatbot_stats(
    place_id: Optional[int] = Query(None),
    date_from: date = Query(None, alias="date_from"),
    date_to: date = Query(None, alias="date_to"),
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Chatbot stats derived from ChatMessage model."""
    from src.models.chat_message import ChatMessage
    
    # Note: ChatMessage doesn't currently link to place_id, 
    # so we filter by owner's activity in general or user_id if needed.
    # For now, we apply date filtering.
    f_date = date_from or start_date
    t_date = date_to or end_date

    query = db.query(func.count(ChatMessage.id))
    if f_date:
        query = query.filter(func.date(ChatMessage.created_at) >= f_date)
    if t_date:
        query = query.filter(func.date(ChatMessage.created_at) <= t_date)
    total_queries = query.scalar() or 0
    success_rate = 100.0 if total_queries > 0 else 0.0
    return {"queries": total_queries, "success_rate": success_rate}


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@router.get("/reviews")
def get_owner_reviews(
    place_id: Optional[int] = Query(None),
    date_from: date = Query(None, alias="date_from"),
    date_to: date = Query(None, alias="date_to"),
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Get aggregated review sentiment stats."""
    target_place_id = resolve_target_place_id(db, current_user.id, place_id)
    
    f_date = date_from or start_date
    t_date = date_to or end_date

    query = db.query(Review.sentiment, func.count(Review.id)).filter(
        Review.place_id == target_place_id
    )
    if f_date:
        query = query.filter(func.date(Review.created_at) >= f_date)
    if t_date:
        query = query.filter(func.date(Review.created_at) <= t_date)
    results = query.group_by(Review.sentiment).all()

    stats = {"positive": 0, "negative": 0, "neutral": 0, "unknown": 0}
    for sentiment, count in results:
        if sentiment in stats:
            stats[sentiment] = count
        elif sentiment is None:
            stats["unknown"] = count
        else:
            stats["neutral"] = count
    return stats


# ---------------------------------------------------------------------------
# Location Heatmap
# ---------------------------------------------------------------------------

@router.get("/location-heatmap")
async def get_location_heatmap(
    uow: Annotated[Any, Depends(get_uow)],
    place_id: Optional[int] = Query(None),
    current_user=Depends(owner_guard),
):
    """AI heatmap from the owner's place visit data."""
    with uow:
        target_place_id = resolve_target_place_id(uow.session, current_user.id, place_id)
        visits = uow.interaction_repository.get_visits_by_place(target_place_id)
        if not visits:
            return []

        # Heatmap only needs lat, lon, cluster  (uses "visits" key)
        points = [
            {
                "lat":     v.user_lat,
                "lon":     v.user_lon,
                "cluster": v.cluster_id,
            }
            for v in visits
            if v.user_lat is not None
            and v.user_lon is not None
            and v.cluster_id is not None
        ]

    from src.services.ai_location_service import ai_location_service
    return await ai_location_service.get_heatmap(points)

@router.get("/active-visitors")
async def get_active_visitors(
    uow: Annotated[Any, Depends(get_uow)],
    place_id: Optional[int] = Query(None),
    current_user=Depends(owner_guard),
):
    with uow:
        target_place_id = resolve_target_place_id(uow.session, current_user.id, place_id)
        visits = uow.interaction_repository.get_visits_by_place(target_place_id)
        if not visits: return []
        points = [
            {
                "lat": v.user_lat, 
                "lon": v.user_lon, 
                "cluster": v.cluster_id, 
                "visited_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in visits
            if v.user_lat is not None and v.user_lon is not None and v.cluster_id is not None
        ]

    from src.services.ai_location_service import ai_location_service
    return await ai_location_service.get_active_visitors(points)

@router.get("/peak-hour")
async def get_peak_hour(
    uow: Annotated[Any, Depends(get_uow)],
    place_id: Optional[int] = Query(None),
    current_user=Depends(owner_guard),
):
    with uow:
        target_place_id = resolve_target_place_id(uow.session, current_user.id, place_id)
        visits = uow.interaction_repository.get_visits_by_place(target_place_id)
        if not visits: return {}
        points = [
            {
                "lat": v.user_lat, 
                "lon": v.user_lon, 
                "cluster": v.cluster_id, 
                "visited_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in visits
            if v.user_lat is not None and v.user_lon is not None and v.cluster_id is not None
        ]

    from src.services.ai_location_service import ai_location_service
    return await ai_location_service.get_peak_hour(points)

@router.get("/location-summary")
async def get_location_summary(
    uow: Annotated[Any, Depends(get_uow)],
    place_id: Optional[int] = Query(None),
    current_user=Depends(owner_guard),
):
    with uow:
        target_place_id = resolve_target_place_id(uow.session, current_user.id, place_id)
        visits = uow.interaction_repository.get_visits_by_place(target_place_id)
        if not visits: return {}
        points = [
            {
                "lat": v.user_lat, 
                "lon": v.user_lon, 
                "cluster": v.cluster_id, 
                "visited_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in visits
            if v.user_lat is not None and v.user_lon is not None and v.cluster_id is not None
        ]

    from src.services.ai_location_service import ai_location_service
    return await ai_location_service.get_owner_summary(points)


# ---------------------------------------------------------------------------
# Opportunities
# ---------------------------------------------------------------------------

@router.get("/opportunities")
async def get_opportunities(
    uow: Annotated[Any, Depends(get_uow)],
    place_id: Optional[int] = Query(None),
    current_user=Depends(owner_guard),
):
    """AI business opportunities from the owner's visit data."""
    with uow:
        target_place_id = resolve_target_place_id(uow.session, current_user.id, place_id)
        place = uow.place_repository.get_by_id(target_place_id)
        
        visits = uow.interaction_repository.get_visits_by_place(target_place_id)
        if not visits:
            return []

        category_name = (
            place.category.name if (place and place.category) else "General"
        )
        district_name = (
            place.address.split(",")[0].strip()
            if (place and place.address)
            else "Beni Suef"
        )

        # Opportunities needs lat, lon, cluster, category, district ("places" key)
        points = [
            {
                "lat":      v.user_lat,
                "lon":      v.user_lon,
                "cluster":  v.cluster_id,
                "category": category_name,
                "district": district_name,
            }
            for v in visits
            if v.user_lat is not None
            and v.user_lon is not None
            and v.cluster_id is not None
        ]

    from src.services.ai_location_service import ai_location_service
    return await ai_location_service.get_opportunities(points)


# ---------------------------------------------------------------------------
# Interaction scatter map
# ---------------------------------------------------------------------------

@router.get("/interactions-locations")
async def get_interactions_locations(
    uow: Annotated[Any, Depends(get_uow)],
    place_id: Optional[int] = Query(None),
    current_user=Depends(owner_guard),
):
    """All interactions with coordinates for the scatter map."""
    with uow:
        target_place_id = resolve_target_place_id(uow.session, current_user.id, place_id)
        interactions = uow.interaction_repository.get_by_place(target_place_id)
        return [
            {
                "lat": i.user_lat, 
                "lon": i.user_lon, 
                "type": i.type,
                "user_id": i.user_id,
                "timestamp": i.created_at.isoformat() if i.created_at else None,
                "cluster": i.cluster_id
            }
            for i in interactions
            if i.user_lat is not None and i.user_lon is not None
        ]


# ---------------------------------------------------------------------------
# Location clusters
# ---------------------------------------------------------------------------

@router.get("/clusters")
async def get_ai_clusters(current_user=Depends(owner_guard)):
    """All available location clusters from the AI service."""
    from src.services.ai_location_service import ai_location_service
    return await ai_location_service.get_clusters()


# ---------------------------------------------------------------------------
# BATCH — Owner anomalies  (PLACE + USER anomalies for this owner's place)
# ---------------------------------------------------------------------------

@router.get("/anomalies")
async def get_anomalies(
    uow: Annotated[Any, Depends(get_uow)],
    place_id: Optional[int] = Query(None),
    current_user=Depends(owner_guard),
):
    # ...
    with uow:
        target_place_id = resolve_target_place_id(uow.session, current_user.id, place_id)
        interactions = uow.interaction_repository.get_by_place(target_place_id)
        cleaned_visits = prepare_user_visits(interactions)

    if not cleaned_visits:
        logger.info(f"[get_anomalies] No valid visits for place_id={target_place_id}")
        return []

    from src.services.anomaly_service import ai_anomaly_service
    return await ai_anomaly_service.detect_anomalies(cleaned_visits)


# ---------------------------------------------------------------------------
# BATCH — Owner anomalies summary (metrics summary for this place)
# ---------------------------------------------------------------------------

@router.get("/anomalies/summary")
async def get_anomalies_summary(
    uow: Annotated[Any, Depends(get_uow)],
    place_id: Optional[int] = Query(None),
    current_user=Depends(owner_guard),
):
    # ...
    with uow:
        target_place_id = resolve_target_place_id(uow.session, current_user.id, place_id)
        interactions = uow.interaction_repository.get_by_place(target_place_id)

        if not interactions:
            return {
                "total_anomalies": 0,
                "urgent_anomalies": 0,
                "summary": "No interactions recorded for your place yet.",
                "details": [],
            }

        # --- First try: get place-specific anomalies from AI ---
        place_visits = prepare_user_visits(interactions)

    from src.services.anomaly_service import ai_anomaly_service

    place_anomalies = []
    if place_visits:
        place_anomalies = await ai_anomaly_service.get_place_anomalies(
            target_place_id, place_visits
        )

    # --- Fallback: run detect_anomalies if no historical records found ---
    if not place_anomalies and place_visits:
        logger.info(
            f"[anomalies/summary] No place anomalies from AI for place_id={target_place_id}, "
            "falling back to detect_anomalies"
        )
        place_anomalies = await ai_anomaly_service.detect_anomalies(place_visits)

    if not place_anomalies:
        return {
            "total_anomalies": 0,
            "urgent_anomalies": 0,
            "summary": "No anomalies detected for your place yet.",
            "details": [],
        }

    urgent = sum(
        1
        for a in place_anomalies
        if isinstance(a, dict) and str(a.get("severity", "")).lower() == "high"
    )

    return {
        "total_anomalies": len(place_anomalies),
        "urgent_anomalies": urgent,
        "summary": (
            f"{len(place_anomalies)} anomalies detected, {urgent} high severity."
        ),
        "details": place_anomalies,
    }


# ---------------------------------------------------------------------------
# BATCH — Place anomalies  (owner-scoped, AI /place-anomalies endpoint)
# ---------------------------------------------------------------------------

@router.get("/place-anomalies")
async def get_place_anomalies(
    uow: Annotated[Any, Depends(get_uow)],
    place_id: Optional[int] = Query(None),
    current_user=Depends(owner_guard),
):
    # ...
    with uow:
        target_place_id = resolve_target_place_id(uow.session, current_user.id, place_id)
        interactions = uow.interaction_repository.get_by_place(target_place_id)
        payload = prepare_place_anomaly_payload(target_place_id, interactions)

    if not payload["visits"]:
        return []

    from src.services.anomaly_service import ai_anomaly_service
    return await ai_anomaly_service.get_place_anomalies(
        payload["place_id"], payload["visits"]
    )


# ---------------------------------------------------------------------------
# ADMIN — District-wide anomaly summary
# ---------------------------------------------------------------------------

@router.get("/admin/anomalies/summary")
async def get_admin_anomaly_summary(
    uow: Annotated[Any, Depends(get_uow)],
    current_user=Depends(owner_guard),
):
    """
    GET /api/owner/admin/anomalies/summary

    District-wide aggregation across ALL places in the system.
    Used by the admin dashboard to detect District Spike and Dead Zone
    anomalies, in addition to the usual Bot Behavior / GPS Spoofing signals.

    Uses the last 1 000 valid visits across the entire platform.
    """
    with uow:
        all_visits = uow.interaction_repository.get_all_valid_visits(limit=1000)
        district_visits = prepare_district_data(all_visits)
        metrics = prepare_place_metrics(all_visits)

    from src.services.anomaly_service import ai_anomaly_service

    # Detect anomalies on district-wide data
    anomalies = await ai_anomaly_service.detect_anomalies(district_visits)

    if not anomalies:
        return {
            "total_anomalies": 0,
            "urgent_anomalies": 0,
            "summary": "No district-level anomalies detected.",
            "metrics": metrics,
            "details": [],
        }

    urgent = sum(
        1
        for a in anomalies
        if isinstance(a, dict) and str(a.get("severity", "")).lower() == "high"
    )

    return {
        "total_anomalies": len(anomalies),
        "urgent_anomalies": urgent,
        "summary": f"{len(anomalies)} district-level anomalies detected, {urgent} high severity.",
        "metrics": metrics,
        "details": anomalies,
    }


from pydantic import BaseModel, Field

class DeliveryZone(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., ge=0)

class UpdateDeliveryPrice(BaseModel):
    delivery_price: float = Field(..., ge=0, description="The new delivery price (must be >= 0)")
    is_free_delivery: bool = Field(False, description="Set to true if delivery is currently free")
    delivery_zones: Optional[List[DeliveryZone]] = Field(default_factory=list)

class UpdateWorkingHours(BaseModel):
    working_hours: str = Field(..., description="The new working hours string (e.g. '9:00 AM - 11:00 PM')")


# ---------------------------------------------------------------------------
# Settings (Delivery Price & Working Hours)
# ---------------------------------------------------------------------------

@router.get("/my-place/delivery-price")
def get_delivery_price(
    place_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Get the current delivery price and zones for the owner's place."""
    target_place_id = resolve_target_place_id(db, current_user.id, place_id)
    place = db.query(Place).filter(Place.id == target_place_id).first()
    return {
        "delivery_price": place.delivery_price,
        "is_free_delivery": place.is_free_delivery,
        "delivery_zones": place.delivery_zones or [],
    }

@router.put("/my-place/delivery-price")
def update_delivery_price(
    payload: UpdateDeliveryPrice,
    place_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Update delivery price, free delivery status, and delivery zones for the owner's place."""
    target_place_id = resolve_target_place_id(db, current_user.id, place_id)
    place = db.query(Place).filter(Place.id == target_place_id).first()

    place.delivery_price = payload.delivery_price
    place.is_free_delivery = payload.is_free_delivery
    place.delivery_zones = [z.model_dump() for z in payload.delivery_zones] if payload.delivery_zones else []
    db.commit()
    return {
        "message": "Delivery settings updated successfully",
        "delivery_price": place.delivery_price,
        "is_free_delivery": place.is_free_delivery,
        "delivery_zones": place.delivery_zones,
    }

@router.get("/my-place/working-hours")
def get_working_hours(
    place_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Get the current working hours for the owner's place."""
    target_place_id = resolve_target_place_id(db, current_user.id, place_id)
    place = db.query(Place).filter(Place.id == target_place_id).first()
    return {"working_hours": place.working_hours}

@router.put("/my-place/working-hours")
def update_working_hours(
    payload: UpdateWorkingHours,
    place_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Update the working hours for the owner's place."""
    target_place_id = resolve_target_place_id(db, current_user.id, place_id)
    place = db.query(Place).filter(Place.id == target_place_id).first()
    
    place.working_hours = payload.working_hours
    db.commit()
    return {"message": "Working hours updated successfully", "working_hours": place.working_hours}


from pydantic import BaseModel, Field

class UpdateOrderSettings(BaseModel):
    is_accepting_orders: Optional[bool] = None
    accepts_delivery: Optional[bool] = None
    accepts_takeaway: Optional[bool] = None

@router.get("/my-place/order-settings")
def get_order_settings(
    place_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Get the current order settings (accepting orders, delivery, takeaway) for the owner's place."""
    target_place_id = resolve_target_place_id(db, current_user.id, place_id)
    place = db.query(Place).filter(Place.id == target_place_id).first()
    return {
        "is_accepting_orders": getattr(place, "is_accepting_orders", True),
        "accepts_delivery": getattr(place, "accepts_delivery", True),
        "accepts_takeaway": getattr(place, "accepts_takeaway", True),
    }

@router.put("/my-place/order-settings")
def update_order_settings(
    payload: UpdateOrderSettings,
    place_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Toggle accepting orders, delivery, and takeaway for the owner's place."""
    target_place_id = resolve_target_place_id(db, current_user.id, place_id)
    place = db.query(Place).filter(Place.id == target_place_id).first()

    if payload.is_accepting_orders is not None:
        place.is_accepting_orders = payload.is_accepting_orders
    if payload.accepts_delivery is not None:
        place.accepts_delivery = payload.accepts_delivery
    if payload.accepts_takeaway is not None:
        place.accepts_takeaway = payload.accepts_takeaway

    db.commit()
    return {
        "message": "Order settings updated successfully",
        "is_accepting_orders": place.is_accepting_orders,
        "accepts_delivery": place.accepts_delivery,
        "accepts_takeaway": place.accepts_takeaway,
    }


class UpdateStatus(BaseModel):
    is_open: bool = Field(..., description="Set to true to open the place, false to mark as closed")

@router.put("/my-place/status")
def update_place_status(
    payload: UpdateStatus,
    place_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Toggle the open/closed status for the owner's place. Does not hide the place from the app."""
    target_place_id = resolve_target_place_id(db, current_user.id, place_id)
    place = db.query(Place).filter(Place.id == target_place_id).first()

    place.is_open = payload.is_open
    db.commit()

    status_text = "Open" if place.is_open else "Closed"
    return {"message": f"Place status updated to {status_text}", "is_open": place.is_open}


# ---------------------------------------------------------------------------
# Image management
# ---------------------------------------------------------------------------

@router.post(
    "/places/{place_id}/images",
    response_model=PlaceImageResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_place_image(
    place_id: int,
    image_data: PlaceImageCreate,
    uow=Depends(get_uow),
    current_user=Depends(owner_guard),
):
    """Upload a new image (place or menu) for the owner's place."""
    return place_image_service.add_place_image(uow, place_id, image_data, current_user)


@router.delete("/place-images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_place_image(
    image_id: int,
    uow=Depends(get_uow),
    current_user=Depends(owner_guard),
):
    """Delete an existing image."""
    place_image_service.delete_place_image(uow, image_id, current_user)
    return None


# ---------------------------------------------------------------------------
# Review list
# ---------------------------------------------------------------------------

@router.get("/reviews/list")
def get_owner_review_list(
    place_id: Optional[int] = Query(None),
    date_from: date = Query(None, alias="date_from"),
    date_to: date = Query(None, alias="date_to"),
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    f_date = date_from or start_date
    t_date = date_to or end_date

    # 1. Get target place IDs
    if place_id:
        # Verify ownership
        place = db.query(Place).filter(Place.id == place_id, Place.owner_id == current_user.id).first()
        if not place:
            raise APIException("Place not found or access denied", code=status.HTTP_404_NOT_FOUND)
        place_ids = [place_id]
    else:
        owner_places = db.query(Place.id).filter(Place.owner_id == current_user.id).all()
        place_ids = [p.id for p in owner_places]
    
    if not place_ids:
        return []

    # 2. Query reviews
    query = (
        db.query(
            Review.rating,
            Review.comment,
            Review.sentiment,
            Review.created_at,
            Review.place_id,
            User.full_name,
            Place.name.label("place_name")
        )
        .join(User, Review.user_id == User.id)
        .join(Place, Review.place_id == Place.id)
        .filter(Review.place_id.in_(place_ids))
    )
    if f_date:
        query = query.filter(func.date(Review.created_at) >= f_date)
    if t_date:
        query = query.filter(func.date(Review.created_at) <= t_date)

    reviews = query.order_by(Review.created_at.desc()).all()
    return [
        {
            "rating": r.rating,
            "comment": r.comment,
            "sentiment": r.sentiment,
            "date": r.created_at,
            "user_name": r.full_name,
            "place_name": r.place_name,
            "place_id": r.place_id,
            "stars": "⭐" * int(r.rating),
        }
        for r in reviews
    ]