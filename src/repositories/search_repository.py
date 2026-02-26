from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from src.models.search_history import SearchHistory
from src.repositories.base_repository import BaseRepository

class SearchRepository(BaseRepository[SearchHistory]):
    """Repository for SearchHistory model."""
    
    def __init__(self, session: Session):
        super().__init__(SearchHistory, session)

    def get_recent(self, user_id: int, limit: int = 5) -> List[str]:
        return self.session.query(SearchHistory.query)\
            .filter(SearchHistory.user_id == user_id)\
            .order_by(SearchHistory.created_at.desc())\
            .distinct().limit(limit).all()

    def get_trending(self, limit: int = 5) -> List[dict]:
        results = self.session.query(
            SearchHistory.query, 
            func.count(SearchHistory.query).label("count")
        ).group_by(SearchHistory.query)\
         .order_by(desc("count"))\
         .limit(limit).all()
        return [{"query": r[0], "count": r[1]} for r in results]
