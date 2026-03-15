from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.core.dependencies import get_db
from src.models.review import Review
from src.models.place import Place
from src.schemas.place import PlaceResponse
from src.models.interaction import Interaction
from src.api.dashboard.dependencies import owner_guard
from typing import List, Dict, Any
from typing import Annotated
from datetime import datetime, timedelta, date
from src.schemas.place_image import PlaceImageCreate, PlaceImageResponse
from src.services import place_image_service
from src.core.dependencies import get_uow, get_place_image_repository

router = APIRouter(dependencies=[Depends(owner_guard)])

def get_owner_place_id(db: Session, owner_id: int):
    place = db.query(Place).filter(Place.owner_id == owner_id).first()
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No place found for this owner"
        )
    return place.id

from src.core.exceptions import APIException
from src.core.logger import logger
import traceback

@router.get("/my-place", response_model=PlaceResponse)
def get_my_place(
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Return the current owner's place details."""
    try:
        place = db.query(Place).filter(Place.owner_id == current_user.id).first()
        if not place:
            raise APIException("No place found for this owner", code=status.HTTP_404_NOT_FOUND)
        
        # Validate schema while database session is active to avoid DetachedInstanceError
        return PlaceResponse.model_validate(place)
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error in get_my_place: {traceback.format_exc()}")
        raise APIException(f"Internal error fetching place: {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/dashboard")
def get_owner_dashboard(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get high-level KPI metrics from real interactions."""
    try:
        place_id = get_owner_place_id(db, current_user.id)

        query = db.query(
            Interaction.type,
            func.count(Interaction.id)
        ).filter(
            Interaction.place_id == place_id
        )

        if start_date:
            query = query.filter(Interaction.created_at >= start_date)

        if end_date:
            query = query.filter(Interaction.created_at <= end_date)

        results = query.group_by(Interaction.type).all()

        stats = {
            "visits": 0,
            "orders": 0,
            "saves": 0,
            "calls": 0,
            "directions": 0
        }

        for type_, count in results:
            if type_ == "visit":
                stats["visits"] = count
            elif type_ == "order":
                stats["orders"] = count
            elif type_ == "save":
                stats["saves"] = count
            elif type_ == "call":
                stats["calls"] = count
            elif type_ == "direction":
                stats["directions"] = count

        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_owner_dashboard: {traceback.format_exc()}")
        raise APIException(f"Dashboard failed: {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/analytics")
def get_owner_analytics(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get real time-series analytics data grouped by day."""
    try:
        place_id = get_owner_place_id(db, current_user.id)
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).date()

        # Query interactions grouped by date and type
        results = db.query(
            func.date(Interaction.created_at).label('day'),
            Interaction.type,
            func.count(Interaction.id).label('count')
        ).filter(
            Interaction.place_id == place_id,
            Interaction.created_at >= start_date,
            Interaction.created_at <= end_date
        ).group_by(
            func.date(Interaction.created_at),
            Interaction.type
        ).all()

        # Format into a list of daily dicts for the dashboard
        daily_data = {}
        
        # Initialize days
        start_dt = start_date
        end_dt = end_date
        curr = start_dt
        while curr <= end_dt:
            d_str = curr.strftime("%Y-%m-%d")
            daily_data[d_str] = {
                "date": d_str,
                "visits": 0, "orders": 0, "saves": 0, "directions": 0, "calls": 0
            }
            curr += timedelta(days=1)

        for day, type_, count in results:
            d_str = day.strftime("%Y-%m-%d")
            if d_str in daily_data:
                key = f"{type_}s" if not type_.endswith('s') else type_
                if type_ == 'visit': key = "visits"
                if type_ == 'direction': key = "directions"
                if d_str in daily_data and key in daily_data[d_str]:
                    daily_data[d_str][key] = count

        return sorted(list(daily_data.values()), key=lambda x: x['date'])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_owner_analytics: {traceback.format_exc()}")
        raise APIException(f"Analytics failed: {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/chatbot-stats")
def get_chatbot_stats(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Chatbot stats - for now keeping simple as metrics aren't in interactions yet."""
    return {
        "queries": 0,
        "success_rate": 0.0
    }

@router.get("/reviews")
def get_owner_reviews(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get real aggregated review sentiment stats."""
    place_id = get_owner_place_id(db, current_user.id)
        
    query = db.query(Review).filter(Review.place_id == place_id)
    if start_date: query = query.filter(Review.created_at >= start_date)
    if end_date: query = query.filter(Review.created_at <= end_date)
    
    results = db.query(
        Review.sentiment,
        func.count(Review.id)
    ).filter(
        Review.place_id == place_id
    ).group_by(Review.sentiment).all()
    
    stats = {"positive": 0, "negative": 0}
    for sentiment, count in results:
        if sentiment in stats:
            stats[sentiment] = count
            
    return stats

@router.get("/location-heatmap")
async def get_location_heatmap(
    uow: Annotated[Any, Depends(get_uow)],
    current_user = Depends(owner_guard)
):
    """Get location activity data from real visits using AI heatmap service."""
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place:
            return []
        
        visits = uow.interaction_repository.get_visits_by_place(place.id)
        if not visits:
            return []

        points = [{"lat": v.user_lat, "lon": v.user_lon} for v in visits]
        heatmap_data = await ai_connector.get_heatmap(points)
        return heatmap_data

# --- IMAGE MANAGEMENT ---

@router.post("/places/{place_id}/images", response_model=PlaceImageResponse, status_code=status.HTTP_201_CREATED)
def upload_place_image(
    place_id: int,
    image_data: PlaceImageCreate,
    uow = Depends(get_uow),
    current_user = Depends(owner_guard)
):
    """Upload a new image (place or menu) for the owner's place."""
    return place_image_service.add_place_image(uow, place_id, image_data, current_user)

@router.delete("/place-images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_place_image(
    image_id: int,
    uow = Depends(get_uow),
    current_user = Depends(owner_guard)
):
    """Delete an existing image."""
    place_image_service.delete_place_image(uow, image_id, current_user)
    return None
