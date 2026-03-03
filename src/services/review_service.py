from typing import Any, List, Optional, Tuple, Dict
from src.core.unit_of_work import UnitOfWork
from src.repositories.review_repository import ReviewRepository
from src.repositories.place_repository import PlaceRepository
from src.schemas.review import ReviewCreate, ReviewUpdate
from src.core.exceptions import APIException
from src.core.permissions import require_place_owner_or_admin
from fastapi import status

def create_review(uow: UnitOfWork, user_id: int, review_data: ReviewCreate):
    with uow:
        # Check if place exists
        place = uow.place_repository.get_by_id(review_data.place_id)
        if not place:
            raise APIException("Place not found", code=status.HTTP_404_NOT_FOUND)

        # Check if user already reviewed
        existing = uow.review_repository.get_user_review_for_place(user_id, review_data.place_id)
        if existing:
            raise APIException("You have already reviewed this place", code=status.HTTP_400_BAD_REQUEST)

        # Create review
        from src.models.review import Review # Lazy import to avoid model dependency in signature
        new_review = Review(
            user_id=user_id,
            place_id=review_data.place_id,
            rating=review_data.rating,
            comment=review_data.comment
        )
        uow.review_repository.create(new_review)
        uow.session.flush() # Ensure ID is generated for stats if needed (though not needed for stats)

        # Update place rating
        _update_place_rating_internal(uow, review_data.place_id)
        
        uow.commit()
        return new_review

def get_place_reviews(repo: ReviewRepository, place_id: int, page: int = 1, page_size: int = 10) -> dict:
    items, total = repo.get_paginated(place_id, page, page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

def get_user_reviews(repo: ReviewRepository, user_id: int, page: int = 1, page_size: int = 10) -> dict:
    items, total = repo.get_user_paginated(user_id, page, page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

def get_review_by_id(repo: ReviewRepository, review_id: int):
    review = repo.get_by_id(review_id)
    if not review:
        raise APIException("Review not found", code=status.HTTP_404_NOT_FOUND)
    return review

def update_review(uow: UnitOfWork, review_id: int, current_user: Any, review_data: ReviewUpdate):
    with uow:
        review = uow.review_repository.get_by_id(review_id)
        if not review:
            raise APIException("Review not found", code=status.HTTP_404_NOT_FOUND)
        
        # Only the reviewer can update their own review
        if review.user_id != current_user.id:
            raise APIException("Not authorized", code=status.HTTP_403_FORBIDDEN)

        if review_data.rating is not None:
            review.rating = review_data.rating
        if review_data.comment is not None:
            review.comment = review_data.comment

        _update_place_rating_internal(uow, review.place_id)
        
        uow.commit()
        return uow.review_repository.get_by_id(review_id)

def delete_review(uow: UnitOfWork, review_id: int, current_user: Any):
    with uow:
        review = uow.review_repository.get_by_id(review_id)
        if not review:
            raise APIException("Review not found", code=status.HTTP_404_NOT_FOUND)
        
        # Authorization check:
        # A review can be deleted by: 
        # 1. The original reviewer
        # 2. The place owner (or admin)
        if review.user_id != current_user.id:
            place = uow.place_repository.get_by_id(review.place_id)
            if not place:
                 raise APIException("Place not found", code=status.HTTP_404_NOT_FOUND)
            require_place_owner_or_admin(current_user, place)

        place_id = review.place_id
        uow.review_repository.delete(review_id)
        
        _update_place_rating_internal(uow, place_id)
        
        uow.commit()
        return True

def _update_place_rating_internal(uow: UnitOfWork, place_id: int):
    """Internal helper to recalculate place rating using transactional session."""
    avg_rating, review_count = uow.review_repository.get_rating_stats(place_id)
    place = uow.place_repository.get_by_id(place_id)
    if place:
        place.rating = round(float(avg_rating), 1)
        place.review_count = int(review_count)
