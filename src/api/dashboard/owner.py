from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.core.dependencies import get_db
from src.services.ai_service import ai_connector
from src.models.user import User
from src.models.review import Review
from src.models.place import Place
from src.schemas.place import PlaceResponse
from src.models.interaction import Interaction
from src.models.favorite import Favorite
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
            query = query.filter(func.date(Interaction.created_at) >= start_date)

        if end_date:
            query = query.filter(func.date(Interaction.created_at) <= end_date)

        results = query.group_by(Interaction.type).all()

        # 2. Count Favorites (saves) separately to sync with favorites table
        fav_query = db.query(func.count(Favorite.id)).filter(Favorite.place_id == place_id)
        if start_date:
            fav_query = fav_query.filter(func.date(Favorite.created_at) >= start_date)
        if end_date:
            fav_query = fav_query.filter(func.date(Favorite.created_at) <= end_date)
        
        favorite_count = fav_query.scalar() or 0

        stats = {
            "visits": 0,
            "orders": 0,
            "saves": favorite_count, # Use Favorite table for accuracy
            "calls": 0,
            "directions": 0
        }

        for type_, count in results:
            if type_ == "visit":
                stats["visits"] = count
            elif type_ == "order":
                stats["orders"] = count
            elif type_ == "save":
                # Only add if interactions are also tracking it, 
                # but usually mobile app uses Favorites table for 'saves'.
                # To be safe, we prioritize Favorite table as per user observation.
                if favorite_count == 0:
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
            func.date(Interaction.created_at) >= start_date,
            func.date(Interaction.created_at) <= end_date
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

        # Also query favorites for time-series
        fav_results = db.query(
            func.date(Favorite.created_at).label('day'),
            func.count(Favorite.id).label('count')
        ).filter(
            Favorite.place_id == place_id,
            func.date(Favorite.created_at) >= start_date,
            func.date(Favorite.created_at) <= end_date
        ).group_by(
            func.date(Favorite.created_at)
        ).all()

        for day, type_, count in results:
            d_str = day.strftime("%Y-%m-%d")
            if d_str in daily_data:
                key = f"{type_}s" if not type_.endswith('s') else type_
                if type_ == 'visit': key = "visits"
                if type_ == 'direction': key = "directions"
                if type_ == 'save': continue # Skip interaction saves, will use favorites
                
                if d_str in daily_data and key in daily_data[d_str]:
                    daily_data[d_str][key] = count
        
        # Merge favorite data
        for day, count in fav_results:
            d_str = day.strftime("%Y-%m-%d")
            if d_str in daily_data:
                daily_data[d_str]["saves"] = count

        return sorted(list(daily_data.values()), key=lambda x: x['date'])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_owner_analytics: {traceback.format_exc()}")
        raise APIException(f"Analytics failed: {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/chatbot-stats")
def get_chatbot_stats(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Chatbot stats derived from ChatMessage model."""
    from src.models.chat_message import ChatMessage
    
    query = db.query(func.count(ChatMessage.id))
    
    # For now, ChatMessages are user-wide. 
    # In a full multi-tenant system, these would be filtered by place_id.
    
    if start_date:
        query = query.filter(func.date(ChatMessage.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(ChatMessage.created_at) <= end_date)
        
    total_queries = query.scalar() or 0
    
    # Simple success rate logic: if there is a reply, it counts as handled.
    # Our ChatMessage model requires reply if created, so it's 100% for now.
    success_rate = 100.0 if total_queries > 0 else 0.0
    
    return {
        "queries": total_queries,
        "success_rate": success_rate
    }

@router.get("/reviews")
def get_owner_reviews(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get real aggregated review sentiment stats."""
    place_id = get_owner_place_id(db, current_user.id)
        
    query = db.query(
        Review.sentiment,
        func.count(Review.id)
    ).filter(
        Review.place_id == place_id
    )

    if start_date:
        query = query.filter(func.date(Review.created_at) >= start_date)

    if end_date:
        query = query.filter(func.date(Review.created_at) <= end_date)

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

        # Heatmap only requires lat, lon, and cluster
        points = [
            {
                "lat": v.user_lat, 
                "lon": v.user_lon, 
                "cluster": v.cluster_id
            } 
            for v in visits if v.user_lat and v.user_lon
        ]
        
        from src.services.ai_location_service import ai_location_service
        heatmap_data = await ai_location_service.get_heatmap(points)
        return heatmap_data

@router.get("/opportunities")
async def get_opportunities(
    uow: Annotated[Any, Depends(get_uow)],
    current_user = Depends(owner_guard)
):
    """Get opportunity clusters based on interaction points."""
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place: return []
        visits = uow.interaction_repository.get_visits_by_place(place.id)
        if not visits: return []
        # Prepare metadata from the owner's place
        category_name = place.category.name if (place and place.category) else "General"
        district_name = place.address.split(',')[0].strip() if (place and place.address) else "Beni Suef"

        # Opportunities requires lat, lon, cluster, category, and district
        points = [
            {
                "lat": v.user_lat, 
                "lon": v.user_lon, 
                "cluster": v.cluster_id,
                "category": category_name,
                "district": district_name
            } 
            for v in visits if v.user_lat and v.user_lon
        ]
        
        from src.services.ai_location_service import ai_location_service
        ops = await ai_location_service.get_opportunities(points)
        return ops

@router.get("/interactions-locations")
async def get_interactions_locations(
    uow: Annotated[Any, Depends(get_uow)],
    current_user = Depends(owner_guard)
):
    """Get all individual interactions with coordinates for scatter map."""
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place:
            return []
        
        interactions = uow.interaction_repository.get_by_place(place.id)
        
        # Filter and format for the dashboard (only include valid coordinates)
        return [
            {
                "lat": i.user_lat,
                "lon": i.user_lon,
                "type": i.type
            }
            for i in interactions
            if i.user_lat is not None and i.user_lon is not None
        ]

@router.get("/clusters")
async def get_ai_clusters(
    current_user = Depends(owner_guard)
):
    """Get all available location clusters from the AI service."""
    from src.services.ai_location_service import ai_location_service
    return await ai_location_service.get_clusters()

@router.get("/anomalies")
async def get_anomalies(
    uow: Annotated[Any, Depends(get_uow)],
    current_user = Depends(owner_guard)
):
    """Get anomalies based on basic interaction metrics."""
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place: return []
        
        interactions = uow.interaction_repository.get_by_place(place.id)
        
        # Build raw interaction payload for AI /detect endpoint (requires full objects)
        interactions_data = [
            {
                "user_id": i.user_id,
                "place_id": i.place_id,
                "user_lat": i.user_lat or 0.0,
                "user_lon": i.user_lon or 0.0,
                "visited_at": i.created_at.isoformat() if i.created_at else None,
                "cluster": i.cluster_id or 0
            }
            for i in interactions
        ]
        
        from src.services.anomaly_service import ai_anomaly_service
        return await ai_anomaly_service.detect_anomalies(interactions_data)

@router.get("/anomalies/summary")
async def get_anomalies_summary(
    uow: Annotated[Any, Depends(get_uow)],
    current_user = Depends(owner_guard)
):
    """Get summary for anomaly data of the current owner's place."""
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place: return {}
        
        # 1. Fetch real anomalies for the place first (uses AI place-anomalies endpoint)
        from src.services.anomaly_service import ai_anomaly_service
        anomalies = await ai_anomaly_service.get_place_anomalies(place.id)
        
        # 2. If no anomalies found -> return empty summary response
        if not anomalies:
            return {
                "total_anomalies": 0,
                "urgent_anomalies": 0,
                "summary": "No anomalies detected for your place yet.",
                "details": []
            }
        
        # 3. Pass real anomalies to /summary endpoint which expects a list of anomaly objects
        return await ai_anomaly_service.get_summary(anomalies)

@router.get("/place-anomalies")
async def get_place_anomalies(
    uow: Annotated[Any, Depends(get_uow)],
    current_user = Depends(owner_guard)
):
    """Get specific place anomalies."""
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place: return []
        
        from src.services.anomaly_service import ai_anomaly_service
        return await ai_anomaly_service.get_place_anomalies(place.id)

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

@router.get("/reviews/list")
def get_owner_review_list(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):

    place_id = get_owner_place_id(db, current_user.id)

    query = db.query(
        Review.rating,
        Review.comment,
        Review.sentiment,
        Review.created_at,
        User.full_name
    ).join(User, Review.user_id == User.id).filter(
        Review.place_id == place_id
    )

    if start_date:
        query = query.filter(func.date(Review.created_at) >= start_date)

    if end_date:
        query = query.filter(func.date(Review.created_at) <= end_date)

    reviews = query.order_by(
        Review.created_at.desc()
    ).all()

    return [
        {
            "rating": r.rating,
            "comment": r.comment,
            "sentiment": r.sentiment,
            "date": r.created_at,
            "user_name": r.full_name,
            "stars": "⭐" * int(r.rating)
        }
        for r in reviews
    ]