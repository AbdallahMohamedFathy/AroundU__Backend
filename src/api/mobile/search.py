from fastapi import APIRouter, Depends, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.dependencies import get_search_repository, get_uow, get_current_user, get_current_user_optional
from src.models.user import User
from src.services import search_service
from src.schemas.search import SearchResponse, TrendingSearch
from src.core.logger import logger

router = APIRouter()

# ─── 🔍 Main Search API ──────────────────────────────────────────────────────
@router.get("/", response_model=SearchResponse, summary="Perform advanced ranked search")
def search_v2_api(
    q: str = Query(..., min_length=1, max_length=50, description="Search query string"),
    lat: Optional[float] = Query(None, description="Optional user latitude for distance boost"),
    lng: Optional[float] = Query(None, description="Optional user longitude for distance boost"),
    limit: int = Query(20, ge=1, le=50),
    uow=Depends(get_uow),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Production-grade Search Engine with:
    - FTS (Full-Text Search)
    - Trigram Typo Tolerance
    - Prefix Autocomplete Fallback
    - Composite Multi-factor Ranking
    - Automatic Trend & History Tracking
    """
    user_id = current_user.id if current_user else None
    
    # ─── Logging ──────────────────────────────────────────────────────────
    logger.info(f"API Search request: q='{q}', user_id={user_id}, location={lat is not None}")
    
    return search_service.search_places(
        uow, 
        query=q, 
        lat=lat, 
        lng=lng, 
        user_id=user_id,
        limit=limit
    )

# ─── 🕒 Recent Searches ─────────────────────────────────────────────────────
@router.get("/recent", response_model=List[str], summary="Get user's last 10 unique searches")
def recent_searches_api(
    repo=Depends(get_search_repository), 
    current_user: User = Depends(get_current_user)
):
    """Returns the last 10 unique searches deduplicated by time."""
    return search_service.get_recent_searches(repo, user_id=current_user.id, limit=10)

# ─── 🔥 Trending Searches ───────────────────────────────────────────────────
@router.get("/trending", response_model=List[TrendingSearch], summary="Get global trending searches")
def trending_searches_api(
    repo=Depends(get_search_repository),
    limit: int = Query(10, ge=1, le=20)
):
    """Returns the top 10 globally popular search queries."""
    return search_service.get_trending_searches(repo, limit=limit)
