from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, text
from src.models.search_history import SearchHistory
from src.models.search_trend import SearchTrend
from src.repositories.base_repository import BaseRepository

class SearchRepository(BaseRepository[SearchHistory]):
    """Repository for managing user search history and global trending queries."""
    
    def __init__(self, session: Session):
        super().__init__(SearchHistory, session)

    def upsert_search(self, query: str, user_id: Optional[int] = None) -> None:
        """
        Record a search event:
        1. Atomic UPSERT into search_trends (global popularity).
        2. Atomic UPSERT into search_history (user specific recent searches).
        """
        if not query or not query.strip():
            return

        query = query.strip().lower()

        # 1. Update Global Trends (Atomic UPSERT)
        trend_sql = """
            INSERT INTO search_trends (query, count, last_searched_at)
            VALUES (:query, 1, NOW())
            ON CONFLICT (query) DO UPDATE SET 
                count = search_trends.count + 1,
                last_searched_at = EXCLUDED.last_searched_at
        """
        self.session.execute(text(trend_sql), {"query": query})

        # 2. Update User History (Atomic UPSERT)
        if user_id:
            history_sql = """
                INSERT INTO search_history (user_id, query, created_at, updated_at)
                VALUES (:user_id, :query, NOW(), NOW())
                ON CONFLICT (user_id, query) DO UPDATE SET 
                    updated_at = EXCLUDED.updated_at
            """
            self.session.execute(text(history_sql), {"user_id": user_id, "query": query})
        
        self.session.flush()

    def get_recent(self, user_id: int, limit: int = 10) -> List[str]:
        """Return the last 10 unique searches for a specific user."""
        results = self.session.query(SearchHistory.query)\
            .filter(SearchHistory.user_id == user_id)\
            .order_by(SearchHistory.updated_at.desc())\
            .limit(limit).all()
        return [r[0] for r in results]

    def get_trending(self, limit: int = 10) -> List[dict]:
        """
        Return the top trending queries.
        Future optimization: Implement time-decayed scoring.
        """
        results = self.session.query(
            SearchTrend.query, 
            SearchTrend.count
        ).order_by(SearchTrend.count.desc())\
         .limit(limit).all()
        
        return [{"query": r[0], "count": r[1]} for r in results]
