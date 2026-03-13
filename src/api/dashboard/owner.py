from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.core.dependencies import get_db
from src.models.review import Review
from src.models.place import Place
from src.api.dashboard.dependencies import owner_guard
from typing import List, Dict, Any
from datetime import datetime, timedelta

router = APIRouter(dependencies=[Depends(owner_guard)])

@router.get("/dashboard")
def get_owner_dashboard(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get high-level KPI metrics."""
    place = db.query(Place).filter(Place.owner_id == current_user.id).first()
    if not place:
        return {"visits": 0, "orders": 0, "saves": 0, "calls": 0, "directions": 0}
    
    # In a real app, these would come from an Analytics/Events table. 
    # For now, we'll return consistent mock data based on the place ID to simulate personality.
    base = (place.id % 5 + 1) * 10
    return {
        "visits": base * 12,
        "orders": base * 3,
        "saves": base * 2,
        "calls": base * 4,
        "directions": base * 5
    }

@router.get("/analytics")
def get_owner_analytics(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get time-series analytics data."""
    # Simulating 30 days of data
    data = []
    # base_date = func.now() # func.now() is for SQL, not Python datetime
    for i in range(30):
        date_str = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        data.append({
            "date": date_str,
            "visits": 10 + (i % 5),
            "orders": 2 + (i % 3),
            "saves": 1 + (i % 2),
            "calls": i % 4
        })
    return data

@router.get("/chatbot-stats")
def get_chatbot_stats(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get chatbot performance stats."""
    return {
        "queries": 150,
        "success_rate": 88.5
    }

@router.get("/reviews")
def get_owner_reviews(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get aggregated review sentiment stats."""
    place = db.query(Place).filter(Place.owner_id == current_user.id).first()
    if not place:
        return {"positive": 0, "negative": 0}
        
    query = db.query(Review).filter(Review.place_id == place.id)
    if start_date: query = query.filter(Review.created_at >= start_date)
    if end_date: query = query.filter(Review.created_at <= end_date)
    
    positive_count = query.filter(Review.sentiment == 'positive').count()
    negative_count = query.filter(Review.sentiment == 'negative').count()
    
    return {"positive": positive_count, "negative": negative_count}

@router.get("/location-heatmap")
def get_location_heatmap(
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get location activity data for mapping."""
    place = db.query(Place).filter(Place.owner_id == current_user.id).first()
    if not place:
        return []
    
    # Return 5-10 nearby "intensity" points around the owner's place
    return [
        {"lat": place.latitude + 0.001 * i, "lon": place.longitude + 0.001 * i, "intensity": 50 + (i*10)}
        for i in range(5)
    ]
