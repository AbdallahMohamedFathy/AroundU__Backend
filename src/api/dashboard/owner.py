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
from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from src.api.dashboard.dependencies import owner_guard
from src.core.dependencies import get_db, get_uow, get_place_image_repository
from src.core.exceptions import APIException
from src.core.logger import logger
from src.models.favorite import Favorite
from src.models.interaction import Interaction
from src.models.place import Place
from src.models.review import Review
from src.models.user import User
from src.schemas.place import PlaceResponse
from src.schemas.place_image import PlaceImageCreate, PlaceImageResponse
from src.services import place_image_service
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

def get_owner_place_id(db: Session, owner_id: int) -> int:
    place = db.query(Place).filter(Place.owner_id == owner_id).first()
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No place found for this owner",
        )
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


# ---------------------------------------------------------------------------
# Dashboard KPIs
# ---------------------------------------------------------------------------

@router.get("/dashboard")
def get_owner_dashboard(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Get high-level KPI metrics from real interactions."""
    try:
        place_id = get_owner_place_id(db, current_user.id)

        query = db.query(Interaction.type, func.count(Interaction.id)).filter(
            Interaction.place_id == place_id
        )
        if start_date:
            query = query.filter(func.date(Interaction.created_at) >= start_date)
        if end_date:
            query = query.filter(func.date(Interaction.created_at) <= end_date)
        results = query.group_by(Interaction.type).all()

        fav_query = db.query(func.count(Favorite.id)).filter(
            Favorite.place_id == place_id
        )
        if start_date:
            fav_query = fav_query.filter(func.date(Favorite.created_at) >= start_date)
        if end_date:
            fav_query = fav_query.filter(func.date(Favorite.created_at) <= end_date)
        favorite_count = fav_query.scalar() or 0

        stats = {
            "visits": 0,
            "orders": 0,
            "saves": favorite_count,
            "calls": 0,
            "directions": 0,
        }
        for type_, count in results:
            if type_ == "visit":
                stats["visits"] = count
            elif type_ == "order":
                stats["orders"] = count
            elif type_ == "call":
                stats["calls"] = count
            elif type_ == "direction":
                stats["directions"] = count

        return stats

    except HTTPException:
        raise
    except Exception:
        logger.error(f"Error in get_owner_dashboard: {traceback.format_exc()}")
        raise APIException("Dashboard failed", code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# Analytics time-series
# ---------------------------------------------------------------------------

@router.get("/analytics")
def get_owner_analytics(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Get real time-series analytics data grouped by day."""
    try:
        place_id = get_owner_place_id(db, current_user.id)

        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).date()

        results = (
            db.query(
                func.date(Interaction.created_at).label("day"),
                Interaction.type,
                func.count(Interaction.id).label("count"),
            )
            .filter(
                Interaction.place_id == place_id,
                func.date(Interaction.created_at) >= start_date,
                func.date(Interaction.created_at) <= end_date,
            )
            .group_by(func.date(Interaction.created_at), Interaction.type)
            .all()
        )

        daily_data: Dict[str, Dict] = {}
        curr = start_date
        while curr <= end_date:
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

        fav_results = (
            db.query(
                func.date(Favorite.created_at).label("day"),
                func.count(Favorite.id).label("count"),
            )
            .filter(
                Favorite.place_id == place_id,
                func.date(Favorite.created_at) >= start_date,
                func.date(Favorite.created_at) <= end_date,
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
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Chatbot stats derived from ChatMessage model."""
    from src.models.chat_message import ChatMessage

    query = db.query(func.count(ChatMessage.id))
    if start_date:
        query = query.filter(func.date(ChatMessage.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(ChatMessage.created_at) <= end_date)
    total_queries = query.scalar() or 0
    success_rate = 100.0 if total_queries > 0 else 0.0
    return {"queries": total_queries, "success_rate": success_rate}


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@router.get("/reviews")
def get_owner_reviews(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    """Get aggregated review sentiment stats."""
    place_id = get_owner_place_id(db, current_user.id)
    query = db.query(Review.sentiment, func.count(Review.id)).filter(
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


# ---------------------------------------------------------------------------
# Location Heatmap
# ---------------------------------------------------------------------------

@router.get("/location-heatmap")
async def get_location_heatmap(
    uow: Annotated[Any, Depends(get_uow)],
    current_user=Depends(owner_guard),
):
    """AI heatmap from the owner's place visit data."""
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place:
            return []

        visits = uow.interaction_repository.get_visits_by_place(place.id)
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
    current_user=Depends(owner_guard),
):
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place: return []
        visits = uow.interaction_repository.get_visits_by_place(place.id)
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
    current_user=Depends(owner_guard),
):
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place: return {}
        visits = uow.interaction_repository.get_visits_by_place(place.id)
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
    current_user=Depends(owner_guard),
):
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place: return {}
        visits = uow.interaction_repository.get_visits_by_place(place.id)
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
    current_user=Depends(owner_guard),
):
    """AI business opportunities from the owner's visit data."""
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place:
            return []

        visits = uow.interaction_repository.get_visits_by_place(place.id)
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
    current_user=Depends(owner_guard),
):
    """All interactions with coordinates for the scatter map."""
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place:
            return []
        interactions = uow.interaction_repository.get_by_place(place.id)
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
    current_user=Depends(owner_guard),
):
    """
    GET /api/owner/anomalies

    Batch anomaly detection for the current owner's place.
    Detects Traffic Spike, Sudden Drop, Unusual Hours (PLACE)
    and Bot Behavior, GPS Spoofing (USER) from visit history.

    Only clean, fully-populated visit records are sent to the AI.
    """
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place:
            return []

        interactions = uow.interaction_repository.get_by_place(place.id)
        cleaned_visits = prepare_user_visits(interactions)

    if not cleaned_visits:
        logger.info(f"[get_anomalies] No valid visits for place_id={place.id}")
        return []

    from src.services.anomaly_service import ai_anomaly_service
    return await ai_anomaly_service.detect_anomalies(cleaned_visits)


# ---------------------------------------------------------------------------
# BATCH — Owner anomalies summary (metrics summary for this place)
# ---------------------------------------------------------------------------

@router.get("/anomalies/summary")
async def get_anomalies_summary(
    uow: Annotated[Any, Depends(get_uow)],
    current_user=Depends(owner_guard),
):
    """
    GET /api/owner/anomalies/summary

    Returns aggregated metric summary for the owner's place.
    Payload shape for AI /summary endpoint:
      [{"metric_name": str, "value": int}, ...]
    """
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place:
            return {"total_anomalies": 0, "urgent_anomalies": 0, "summary": "No place found.", "details": []}

        interactions = uow.interaction_repository.get_by_place(place.id)

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
            place.id, place_visits
        )

    # --- Fallback: run detect_anomalies if no historical records found ---
    if not place_anomalies and place_visits:
        logger.info(
            f"[anomalies/summary] No place anomalies from AI for place_id={place.id}, "
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
    current_user=Depends(owner_guard),
):
    """
    GET /api/owner/place-anomalies

    Calls the AI /place-anomalies endpoint with the correct payload:
      {"place_id": int, "visits": [...]}
    """
    with uow:
        place = uow.place_repository.get_by_owner_id(current_user.id)
        if not place:
            return []

        interactions = uow.interaction_repository.get_by_place(place.id)
        payload = prepare_place_anomaly_payload(place.id, interactions)

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
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(owner_guard),
):
    place_id = get_owner_place_id(db, current_user.id)
    query = (
        db.query(
            Review.rating,
            Review.comment,
            Review.sentiment,
            Review.created_at,
            User.full_name,
        )
        .join(User, Review.user_id == User.id)
        .filter(Review.place_id == place_id)
    )
    if start_date:
        query = query.filter(func.date(Review.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(Review.created_at) <= end_date)

    reviews = query.order_by(Review.created_at.desc()).all()
    return [
        {
            "rating": r.rating,
            "comment": r.comment,
            "sentiment": r.sentiment,
            "date": r.created_at,
            "user_name": r.full_name,
            "stars": "⭐" * int(r.rating),
        }
        for r in reviews
    ]