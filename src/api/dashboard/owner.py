from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.core.dependencies import get_db
from src.models.review import Review
from src.models.place import Place
from src.models.interaction import Interaction
from src.api.dashboard.dependencies import owner_guard
from typing import List, Dict, Any
from datetime import datetime, timedelta

router = APIRouter(dependencies=[Depends(owner_guard)])

def get_owner_place_id(db: Session, owner_id: int):
    place = db.query(Place).filter(Place.owner_id == owner_id).first()
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No place found for this owner"
        )
    return place.id

@router.get("/my-place")
def get_my_place(
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Return the current owner's place details."""
    place = db.query(Place).filter(Place.owner_id == current_user.id).first()
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No place found for this owner"
        )
    return place

@router.get("/dashboard")
def get_owner_dashboard(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get high-level KPI metrics from real interactions."""
    place_id = get_owner_place_id(db, current_user.id)
    
    query = db.query(Interaction).filter(Interaction.place_id == place_id)
    if start_date: query = query.filter(Interaction.created_at >= start_date)
    if end_date: query = query.filter(Interaction.created_at <= end_date)
    
    # Aggregate counts
    interactions = query.all()
    
    stats = {
        "visits": 0,
        "orders": 0,
        "saves": 0,
        "calls": 0,
        "directions": 0
    }
    
    for inter in interactions:
        key = f"{inter.type}s" if not inter.type.endswith('s') else inter.type
        if inter.type == 'direction': key = "directions"
        if inter.type == 'visit': key = "visits"
        if inter.type == 'call': key = "calls"
        if inter.type == 'order': key = "orders"
        if inter.type == 'save': key = "saves"
        
        if key in stats:
            stats[key] += 1
            
    return stats

@router.get("/analytics")
def get_owner_analytics(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get real time-series analytics data grouped by day."""
    place_id = get_owner_place_id(db, current_user.id)
    
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

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
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
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
def get_location_heatmap(
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """Get location activity data from real visits (simulated by random jitter around place for heat effect)."""
    place = db.query(Place).filter(Place.owner_id == current_user.id).first()
    if not place:
        return []
    
    # We query interactions of type 'visit' for this place
    visits = db.query(Interaction).filter(
        Interaction.place_id == place.id,
        Interaction.type == 'visit'
    ).count()

    if visits == 0:
        return []

    # Since we don't have user coordinates in Interaction (yet), 
    # we return spread points around the place to show "activity area"
    return [
        {"lat": place.latitude + (i*0.0005), "lon": place.longitude + (j*0.0005), "intensity": visits * (i+j+1)}
        for i in range(-2, 3) for j in range(-2, 3)
    ]
