from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.core.dependencies import get_db
from src.models.review import Review
from src.models.place import Place
from src.api.dashboard.dependencies import owner_guard

router = APIRouter(dependencies=[Depends(owner_guard)])

@router.get("/reviews")
def get_owner_reviews(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(owner_guard)
):
    """
    Get aggregated review sentiment stats for the owner's places.
    """
    # Find places owned by this user
    place_ids = db.query(Place.id).filter(Place.owner_id == current_user.id).all()
    place_ids = [p[0] for p in place_ids]
    
    if not place_ids:
        return {"positive": 0, "negative": 0}
        
    query = db.query(Review).filter(Review.place_id.in_(place_ids))
    
    if start_date:
        query = query.filter(Review.created_at >= start_date)
    if end_date:
        query = query.filter(Review.created_at <= end_date)
        
    # Aggregate sentiment
    positive_count = query.filter(Review.sentiment == 'positive').count()
    negative_count = query.filter(Review.sentiment == 'negative').count()
    
    return {
        "positive": positive_count,
        "negative": negative_count
    }
