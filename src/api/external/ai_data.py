from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from src.core.database import get_db
from src.core.dependencies import verify_ai_service, limiter
from src.schemas.ai_schemas import AIInteractionResponse, AIPlaceResponse, AIAnalyticsResponse
from src.models.interaction import Interaction
from src.models.place import Place

router = APIRouter(prefix="/ai/data", tags=["AI Gateway"])

@router.get("/interactions", response_model=dict)
@limiter.limit("20/minute")
async def get_interactions(
    request: Request,
    skip: int = 0, 
    limit: int = 100,
    service = Depends(verify_ai_service("read:interactions")),
    db: Session = Depends(get_db)
):
    """Fetch sanitized user interactions."""
    limit = min(limit, 100) # Hard cap limit
    # Just a simple query for demonstration
    interactions = db.query(Interaction).order_by(Interaction.created_at.desc()).offset(skip).limit(limit).all()
    
    # We would map Interaction to AIInteractionResponse
    # Since this is a demo structure, we'll return an empty list or mock if table is empty
    return {
        "data": [
            AIInteractionResponse(
                user_id=str(i.user_id),
                event_type=i.interaction_type,
                place_id=str(i.place_id) if i.place_id else None,
                rating_value=None,
                timestamp=i.created_at
            ) for i in interactions
        ],
        "meta": {"limit": limit, "skip": skip}
    }

@router.get("/places", response_model=dict)
@limiter.limit("20/minute")
async def get_places(
    request: Request,
    category: str = None,
    skip: int = 0, 
    limit: int = 100,
    service = Depends(verify_ai_service("read:places")),
    db: Session = Depends(get_db)
):
    """Fetch sanitized places metadata."""
    limit = min(limit, 100)
    query = db.query(Place)
    if category:
        # Assuming place has a category relationship or field. 
        # Using string matching or category ID based on the DB schema.
        pass
        
    places = query.offset(skip).limit(limit).all()
    
    return {
        "data": [
            AIPlaceResponse(
                place_id=str(p.id),
                name=p.name,
                category="Unknown", # p.category.name if p.category else "Unknown"
                rating=p.rating or 0.0,
                review_count=p.reviews_count or 0,
                lat=p.latitude,
                lng=p.longitude
            ) for p in places
        ],
        "meta": {"limit": limit, "skip": skip}
    }

@router.get("/analytics", response_model=AIAnalyticsResponse)
@limiter.limit("10/minute")
async def get_analytics(
    request: Request,
    service = Depends(verify_ai_service("read:analytics")),
    db: Session = Depends(get_db)
):
    """Pre-computed analytics for AI."""
    # This should be cached in Redis in production
    return AIAnalyticsResponse(
        top_rated_places=[],
        most_visited_places=[],
        trending_categories=["COFFEE", "RESTAURANT"]
    )
