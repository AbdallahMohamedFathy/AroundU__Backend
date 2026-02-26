from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from src.models.place import Place
from src.repositories.base_repository import BaseRepository

class PlaceRepository(BaseRepository[Place]):
    """Repository for Place model with optimized nearby search."""
    
    def __init__(self, session: Session):
        super().__init__(Place, session)

    def get_by_id_with_details(self, place_id: int) -> Optional[Place]:
        """Get place with category eager loaded to prevent N+1."""
        return self.session.query(Place)\
            .options(joinedload(Place.category))\
            .filter(Place.id == place_id).first()

    def get_nearby(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float, 
        category_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Place]:
        """
        Retrieves places within a bounding box (SQL FILTERING).
        This is significantly faster than calculating Haversine distance for all rows.
        """
        # Roughly 1 degree of latitude is 111km
        lat_delta = radius_km / 111.0
        # Longitude delta depends on latitude
        import math
        lng_delta = radius_km / (111.0 * math.cos(math.radians(latitude)))

        min_lat, max_lat = latitude - lat_delta, latitude + lat_delta
        min_lng, max_lng = longitude - lng_delta, longitude + lng_delta

        query = self.session.query(Place).options(joinedload(Place.category))
        
        # SQL-level bounding box filtering
        query = query.filter(
            Place.latitude.between(min_lat, max_lat),
            Place.longitude.between(min_lng, max_lng)
        )

        if category_id:
            query = query.filter(Place.category_id == category_id)

        return query.offset(offset).limit(limit).all()

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[int] = None,
        is_active: bool = True,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        """Advanced filtered, sorted, and paginated query."""
        from sqlalchemy import desc, asc
        
        query = self.session.query(Place).options(joinedload(Place.category))
        
        if category_id:
            query = query.filter(Place.category_id == category_id)
        if is_active is not None:
            query = query.filter(Place.is_active == is_active)

        # Apply sorting
        col = getattr(Place, sort_by, Place.created_at)
        query = query.order_by(desc(col) if sort_order == "desc" else asc(col))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return items, total

    def search(self, query: Optional[str] = None, category: Optional[str] = None) -> List[Place]:
        from sqlalchemy import or_
        from src.models.category import Category
        
        stmt = self.session.query(Place).join(Category)
        
        if query:
            search_filter = or_(
                Place.name.ilike(f"%{query}%"),
                Place.description.ilike(f"%{query}%"),
                Category.name.ilike(f"%{query}%")
            )
            stmt = stmt.filter(search_filter)
            
        if category:
            stmt = stmt.filter(Category.name.ilike(f"%{category}%"))
            
        return stmt.order_by(Place.rating.desc()).all()
