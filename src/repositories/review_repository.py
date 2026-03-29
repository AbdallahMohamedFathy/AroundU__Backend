from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from src.models.review import Review
from src.repositories.base_repository import BaseRepository

class ReviewRepository(BaseRepository[Review]):
    """Repository for Review model."""
    
    def __init__(self, session: Session):
        super().__init__(Review, session)

    def get_by_id(self, id: int) -> Optional[Review]:
        return (
            self.session.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.id == id)
            .first()
        )

    def get_paginated(self, place_id: int, page: int = 1, page_size: int = 10) -> tuple:
        query = (
            self.session.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.place_id == place_id)
            .order_by(Review.created_at.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_user_paginated(self, user_id: int, page: int = 1, page_size: int = 10) -> tuple:
        query = (
            self.session.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.user_id == user_id)
            .order_by(Review.created_at.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_user_review_for_place(self, user_id: int, place_id: int) -> Optional[Review]:
        return self.session.query(Review).filter(
            Review.user_id == user_id,
            Review.place_id == place_id
        ).first()

    def get_rating_stats(self, place_id: int) -> tuple:
        """Calculate average rating and count for a place."""
        from sqlalchemy import func
        result = self.session.query(
            func.avg(Review.rating),
            func.count(Review.id)
        ).filter(Review.place_id == place_id).first()
        return result[0] or 0.0, result[1] or 0
