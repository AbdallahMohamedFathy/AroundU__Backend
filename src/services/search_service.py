"""
Service layer for advanced searching (Refactored for Production Performance)
"""
import time
import logging
from typing import List, Optional, Dict
from src.core.unit_of_work import UnitOfWork
from src.core.logger import logger

def search_places(
    uow: UnitOfWork, 
    query: Optional[str] = None, 
    lat: Optional[float] = None, 
    lng: Optional[float] = None, 
    user_id: Optional[int] = None,
    limit: int = 20
) -> Dict:
    """
    Coordinates advanced search logic:
    1. Validates query.
    2. Performs ranked search with fallbacks (prefix/FTS/fuzzy).
    3. Records search history and updates trends atomically.
    4. Provides "Recommended/Trending" fallbacks if no results found.
    """
    start_time = time.time()
    
    # ─── 0. Handle Empty Query ─────────────────────────────────────
    if not query or not query.strip():
        # Fallback to trending queries if empty
        with uow:
            trending = uow.search_repository.get_trending(limit=10)
            return {"results": [], "fallback": "empty_query", "context": trending}

    query = query.strip()
    
    with uow:
        # ─── 1. Perform Advanced Search ──────────────────────────────
        results = uow.place_repository.search_v2(
            q=query, 
            lat=lat, 
            lng=lng, 
            limit=limit
        )

        fallback_used = False
        if not results:
            # ─── 2. Zero Result Fallback ────────────────────────────
            results = uow.place_repository.get_popular_nearby(lat=lat, lng=lng, limit=5)
            fallback_used = True

        # ─── 3. Record Search History & Trends ─────────────────────
        # Only record if it's a real query (not empty)
        uow.search_repository.upsert_search(query, user_id=user_id)
        uow.commit()

        execution_time = round(time.time() - start_time, 3)
        
        # ─── 4. Structured Logging ─────────────────────────────────
        logger.info({
            "action": "search",
            "query": query,
            "results_count": len(results),
            "execution_time_sec": execution_time,
            "fallback_used": fallback_used,
            "has_location": lat is not None
        })

        return {
            "results": results,
            "metadata": {
                "execution_time": execution_time,
                "count": len(results),
                "fallback": fallback_used
            }
        }

def get_recent_searches(repo, user_id: int, limit: int = 10):
    """Get the last 10 unique searches for the user."""
    return repo.get_recent(user_id, limit)

def get_trending_searches(repo, limit: int = 10):
    """Get the top global trending searches."""
    return repo.get_trending(limit)
