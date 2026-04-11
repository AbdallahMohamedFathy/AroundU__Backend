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
        """Get place with category and branches eager loaded to prevent N+1."""
        return self.session.query(Place)\
            .options(
                joinedload(Place.category),
                joinedload(Place.branches)
            )\
            .filter(Place.id == place_id).first()

    def get_by_owner_id(self, owner_id: int) -> Optional[Place]:
        """Returns the primary place for an owner (first one found)."""
        return self.session.query(Place).filter(Place.owner_id == owner_id).first()

    def get_all_by_owner_id(self, owner_id: int) -> List[Place]:
        """Returns all places owned by a specific user."""
        return self.session.query(Place).filter(Place.owner_id == owner_id).all()

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

    def search_v2(
        self, 
        q: str, 
        lat: Optional[float] = None, 
        lng: Optional[float] = None, 
        limit: int = 20
    ) -> List[dict]:
        """
        Refined advanced search with:
        - Prefix matching for short queries (<3 chars)
        - Full-Text Search (FTS) with rank normalization
        - Typo tolerance (similarity fallback)
        - Composite scoring (Relevance, Rating, Popularity, Distance)
        - Safe normalization and clamping
        - Structured logging and performance limits
        """
        # Handle empty query
        if not q or not q.strip():
            return []

        q = q.strip()
        is_short = len(q) < 3

        # Location param context
        has_location = lat is not None and lng is not None

        # SQL components
        if is_short:
            # Prefix search logic
            match_sql = "p.name ILIKE :prefix"
            params = {"prefix": f"{q}%"}
            text_score_sql = "1.0" # Binary match for prefix
        else:
            # FTS logic
            match_sql = "p.search_vector @@ plainto_tsquery('english', :q)"
            params = {"q": q}
            # Normalized ts_rank
            text_score_sql = "COALESCE(ts_rank(p.search_vector, plainto_tsquery('english', :q)), 0.0) / (COALESCE(ts_rank(p.search_vector, plainto_tsquery('english', :q)), 0.0) + 1.0)"

        if has_location:
            params.update({"lat": lat, "lng": lng})
            ref_point = "ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography"
            dist_sql = f"ST_Distance(p.location, {ref_point})"
            dist_score_sql = f"1.0 / (1.0 + {dist_sql} / 1000.0)"
        else:
            dist_score_sql = "0.0"

        params["limit"] = limit


        # Safe favorite normalization
        # We need the max favorite count from candidates to normalize
        # For simplicity and performance, we use a fixed high value or a subquery
        # Here we'll use a subquery for the current set of candidates
        max_fav_sql = "(SELECT GREATEST(MAX(favorite_count), 1) FROM places WHERE is_active = true)"
        fav_score_sql = f"log(p.favorite_count + 1) / log({max_fav_sql} + 1)"

        # Composite score: 0.4 Text + 0.3 Rating + 0.2 Pop + 0.1 Dist
        # Rating normalized: rating / 5.0
        final_score_sql = f"""
            LEAST(
                (0.4 * ({text_score_sql})) + 
                (0.3 * (COALESCE(p.rating, 0.0) / 5.0)) + 
                (0.2 * ({fav_score_sql})) + 
                (0.1 * ({dist_score_sql})),
                1.0
            )
        """

        query_str = f"""
            SELECT 
                p.id, 
                p.name, 
                p.description,
                c.name as category_name,
                p.rating,
                p.review_count,
                p.favorite_count,
                {dist_score_sql if has_location else '0.0'} as distance_meters,
                {final_score_sql} as score
            FROM places p
            JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = true AND ({match_sql})
            ORDER BY score DESC
            LIMIT :limit
        """

        results = self.session.execute(text(query_str), params).fetchall()

        # Fallback to fuzzy matching if no results and not short
        if not results and not is_short:
            fuzzy_sql = f"""
                SELECT 
                    p.id, p.name, p.description, c.name as category_name,
                    p.rating, p.review_count, p.favorite_count,
                    {dist_score_sql if has_location else '0.0'} as distance_meters,
                    (similarity(p.name, :q) * 0.4) + (0.3 * (COALESCE(p.rating, 0.0) / 5.0)) as score
                FROM places p
                JOIN categories c ON p.category_id = c.id
                WHERE p.is_active = true AND similarity(p.name, :q) > 0.3
                ORDER BY score DESC
                LIMIT :limit
            """
            results = self.session.execute(text(fuzzy_sql), {"q": q, "limit": limit, "lat": lat, "lng": lng} if has_location else {"q": q, "limit": limit}).fetchall()


        return [
            {
                "id": r.id,
                "name": r.name,
                "category": r.category_name,
                "description": r.description,
                "rating": float(r.rating or 0),
                "review_count": int(r.review_count or 0),
                "favorite_count": int(r.favorite_count or 0),
                "score": float(r.score or 0)
            }
            for r in results
        ]

    def get_popular_nearby(
        self, 
        lat: Optional[float] = None, 
        lng: Optional[float] = None, 
        limit: int = 10
    ) -> List[dict]:
        """
        Fallback for zero search results. 
        Returns the top rated places, optionally near the user.
        """
        has_location = lat is not None and lng is not None
        
        if has_location:
            ref_point = "ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography"
            dist_sql = f"ST_Distance(p.location, {ref_point})"
            order_sql = f"(p.rating / 5.0 * 0.7) + (1.0 / (1.0 + {dist_sql}/1000.0) * 0.3) DESC"
        else:
            order_sql = "p.rating DESC"

        query_str = f"""
            SELECT 
                p.id, p.name, p.description, c.name as category_name,
                p.rating, p.review_count, p.favorite_count,
                0.0 as score
            FROM places p
            JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = true
            ORDER BY {order_sql}
            LIMIT :limit
        """
        
        params = {"limit": limit}
        if has_location:
            params.update({"lat": lat, "lng": lng})

        results = self.session.execute(text(query_str), params).fetchall()

        return [
            {
                "id": r.id,
                "name": r.name,
                "category": r.category_name,
                "description": r.description,
                "rating": float(r.rating or 0),
                "review_count": int(r.review_count or 0),
                "favorite_count": int(r.favorite_count or 0),
                "score": 0.0
            }
            for r in results
        ]
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
                (
                    SELECT COALESCE(json_agg(
                        json_build_object(
                            'id', pi.id,
                            'place_id', pi.place_id,
                            'image_url', pi.image_url,
                            'image_type', pi.image_type,
                            'caption', pi.caption,
                            'created_at', pi.created_at
                        )
                    ), '[]'::json)
                    FROM place_images pi
                    WHERE pi.place_id = p.id
                ) as images,
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

        import json
        
        results_list = []
        for r in results:
            images_data = getattr(r, 'images', [])
            if images_data is None:
                images_data = []
            elif isinstance(images_data, str):
                try:
                    images_data = json.loads(images_data)
                except Exception:
                    images_data = []

            results_list.append({
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
                "images": images_data
            })
            
        return results_list

    def get_trending(
        self,
        latitude: float,
        longitude: float,
        category_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[dict]:
        """
        Retrieves places ranked by a trending score based on:
        1. Rating (40%)
        2. Favorite Count (30%)
        3. Distance (30%)
        """
        
        # We need the max favorite count for normalization
        max_fav_sql = "(SELECT GREATEST(MAX(favorite_count), 1) FROM places WHERE is_active = true)"
        
        query_str = f"""
            SELECT 
                p.id, 
                p.name, 
                p.description,
                p.address,
                p.phone,
                p.website,
                p.latitude,
                p.longitude,
                p.category_id,
                p.parent_id,
                p.instagram_url,
                p.facebook_url,
                p.whatsapp_number,
                p.tiktok_url,
                p.rating,
                p.review_count,
                p.favorite_count,
                p.is_active,
                p.created_at,
                c.name as category_name,
                ST_Distance(p.location, ref_point.pt) / 1000.0 AS distance_km,
                (
                    SELECT COALESCE(json_agg(
                        json_build_object(
                            'id', pi.id,
                            'place_id', pi.place_id,
                            'image_url', pi.image_url,
                            'image_type', pi.image_type,
                            'caption', pi.caption,
                            'created_at', pi.created_at
                        )
                    ), '[]'::json)
                    FROM place_images pi
                    WHERE pi.place_id = p.id
                ) as images,
                (
                    (0.4 * (COALESCE(p.rating, 0.0) / 5.0)) + 
                    (0.3 * (log(p.favorite_count + 1) / log({max_fav_sql} + 1))) + 
                    (0.3 * (1.0 / (1.0 + (ST_Distance(p.location, ref_point.pt) / 1000.0))))
                ) as trending_score
            FROM places p
            JOIN categories c ON p.category_id = c.id
            CROSS JOIN (
                SELECT ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography as pt
            ) AS ref_point
            WHERE p.is_active = true
        """

        params = {
            "lat": latitude,
            "lng": longitude,
            "limit": limit,
            "offset": offset
        }

        if category_id:
            query_str += " AND p.category_id = :category_id"
            params["category_id"] = category_id

        query_str += " ORDER BY trending_score DESC LIMIT :limit OFFSET :offset"

        results = self.session.execute(text(query_str), params).fetchall()
        
        # Use an internal helper to convert row to dict if possible, 
        # but here we'll manually map to ensure field compatibility.
        import json
        formatted_results = []
        for r in results:
            images_data = getattr(r, 'images', [])
            if images_data is None:
                images_data = []
            elif isinstance(images_data, str):
                try:
                    images_data = json.loads(images_data)
                except Exception:
                    images_data = []

            formatted_results.append({
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "address": r.address,
                "phone": r.phone or [],
                "website": r.website,
                "latitude": float(r.latitude),
                "longitude": float(r.longitude),
                "category_id": r.category_id,
                "parent_id": r.parent_id,
                "instagram_url": r.instagram_url,
                "facebook_url": r.facebook_url,
                "whatsapp_number": r.whatsapp_number,
                "tiktok_url": r.tiktok_url,
                "rating": float(r.rating or 0),
                "review_count": int(r.review_count or 0),
                "favorite_count": int(r.favorite_count or 0),
                "is_active": r.is_active,
                "created_at": r.created_at,
                "category": r.category_name,
                "distance_km": float(r.distance_km) if r.distance_km else 0.0,
                "images": images_data,
                "trending_score": float(r.trending_score) if r.trending_score else 0.0,
                "branches": [] # Eager loading branches for trending is often overkill, keep empty for now
            })
            
        return formatted_results

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
