from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, text
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

    def get_by_owner_id(self, owner_id: int) -> Optional[Place]:
        return self.session.query(Place).filter(Place.owner_id == owner_id).first()

    def get_nearby(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float, 
        category_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[dict]:
        """
        Retrieves places using PostGIS ST_Distance and ST_DWithin.
        Uses the <-> operator for high-performance index-assisted sorting.
        """
        # Convert radius to meters
        radius_m = radius_km * 1000

        query_str = """
            SELECT 
                p.id, 
                p.name, 
                p.description,
                c.name as category_name,
                ST_Distance(p.location, ref_point.pt) as distance_meters
            FROM places p
            JOIN categories c ON p.category_id = c.id
            CROSS JOIN (
                SELECT ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography as pt
            ) AS ref_point
            WHERE p.is_active = true
            AND ST_DWithin(p.location, ref_point.pt, :radius_m)
        """

        params = {
            "lat": latitude,
            "lng": longitude,
            "radius_m": radius_m,
            "limit": limit,
            "offset": offset
        }

        if category_id:
            query_str += " AND p.category_id = :category_id"
            params["category_id"] = category_id

        # Use index-assisted NN sorting
        query_str += " ORDER BY p.location <-> ref_point.pt LIMIT :limit OFFSET :offset"

        results = self.session.execute(text(query_str), params).fetchall()
        
        # Format results into dictionaries
        return [
            {
                "id": r.id,
                "name": r.name,
                "category": r.category_name,
                "description": r.description,
                "distance": r.distance_meters
            }
            for r in results
        ]

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

    # ─── RECOMMENDATION ENGINE ────────────────────────────────────────
    def get_recommendation_candidates(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        category_id: Optional[int] = None,
        limit: int = 300
    ) -> List[dict]:
        """
        Fetch candidate places for the recommendation engine.
        Uses PostGIS ST_DWithin for radius filtering + KNN (<->) for ordering.
        Returns all fields needed for scoring: rating, review_count, favorite_count, distance_km.
        """
        radius_m = radius_km * 1000

        query_str = """
            SELECT
                p.id,
                p.name,
                p.description,
                p.address,
                p.latitude,
                p.longitude,
                p.rating,
                p.review_count,
                p.favorite_count,
                p.is_active,
                c.name AS category_name,
                ST_Distance(p.location, ref_point.pt) / 1000.0 AS distance_km
            FROM places p
            JOIN categories c ON p.category_id = c.id
            CROSS JOIN (
                SELECT ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography AS pt
            ) AS ref_point
            WHERE p.is_active = true
              AND ST_DWithin(p.location, ref_point.pt, :radius_m)
        """

        params = {
            "lat": latitude,
            "lng": longitude,
            "radius_m": radius_m,
            "limit": limit,
        }

        if category_id:
            query_str += " AND p.category_id = :category_id"
            params["category_id"] = category_id

        # KNN-assisted nearest-neighbor sort, limited to top N candidates
        query_str += " ORDER BY p.location <-> ref_point.pt LIMIT :limit"

        results = self.session.execute(text(query_str), params).fetchall()

        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "address": r.address,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "rating": float(r.rating or 0),
                "review_count": int(r.review_count or 0),
                "favorite_count": int(r.favorite_count or 0),
                "category": r.category_name,
                "distance_km": float(r.distance_km) if r.distance_km else 0.0,
            }
            for r in results
        ]

    def get_global_rating_stats(self) -> dict:
        """
        Return the global average rating and average review count across all active places.
        Used as the Bayesian prior (C value) for the recommendation scoring.
        """
        from sqlalchemy import func
        result = self.session.query(
            func.avg(Place.rating),
            func.avg(Place.review_count),
            func.count(Place.id),
        ).filter(Place.is_active == True).first()  # noqa: E712

        return {
            "global_avg_rating": float(result[0]) if result[0] else 3.0,
            "avg_review_count": float(result[1]) if result[1] else 0.0,
            "total_places": int(result[2]) if result[2] else 0,
        }
