from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy import or_, desc, func
from src.models.place import Place
from src.models.category import Category
from src.models.search_history import SearchHistory
from src.schemas.place import PlaceResponse
from src.schemas.search import TrendingSearch

def search_places(db: Session, query: str = None, category: str = None, user_id: int = None):
    stmt = select(Place).join(Category)
    
    if query:
        # Simple ILIKE search for now. Full Text Search would require TSVector setup.
        search_filter = or_(
            Place.name.ilike(f"%{query}%"),
            Place.description.ilike(f"%{query}%"),
            Category.name.ilike(f"%{query}%")
        )
        stmt = stmt.filter(search_filter)
        
        # Save search history if user is logged in
        if user_id:
            db.add(SearchHistory(user_id=user_id, query=query))
            db.commit()
    
    if category:
        stmt = stmt.filter(Category.name.ilike(f"%{category}%"))
    
    # Sort by rating by default for now
    stmt = stmt.order_by(desc(Place.rating))
    
    result = db.execute(stmt)
    return result.scalars().all()

def get_recent_searches(db: Session, user_id: int, limit: int = 5):
    stmt = select(SearchHistory.query).filter(SearchHistory.user_id == user_id)\
        .order_by(desc(SearchHistory.created_at)).distinct().limit(limit)
    result = db.execute(stmt)
    return result.scalars().all()

def get_trending_searches(db: Session, limit: int = 5):
    # Aggregation to find most common queries
    stmt = select(SearchHistory.query, func.count(SearchHistory.query).label("count"))\
        .group_by(SearchHistory.query)\
        .order_by(desc("count"))\
        .limit(limit)
    result = db.execute(stmt)
    return [{"query": row[0], "count": row[1]} for row in result.all()]
