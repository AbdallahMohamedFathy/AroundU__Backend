from typing import Any
from src.core.unit_of_work import UnitOfWork
from src.repositories.review_repository import ReviewRepository
from src.repositories.place_repository import PlaceRepository
from src.schemas.review import ReviewCreate, ReviewUpdate
from src.core.exceptions import APIException
from src.core.permissions import require_place_owner_or_admin
from fastapi import status
from src.services.sentiment_service import analyze_sentiment


def create_review(uow: UnitOfWork, user_id: int, review_data: ReviewCreate):

    with uow:

        # Check place exists
        place = uow.place_repository.get_by_id(review_data.place_id)
        if not place:
            raise APIException("Place not found", code=status.HTTP_404_NOT_FOUND)

        # Check duplicate review
        existing = uow.review_repository.get_user_review_for_place(
            user_id,
            review_data.place_id
        )

        if existing:
            raise APIException(
                "You have already reviewed this place",
                code=status.HTTP_400_BAD_REQUEST
            )

        # -----------------------------
        # Sentiment Analysis
        # -----------------------------
        sentiment_result = None

        if review_data.comment:
            try:
                sentiment_result = analyze_sentiment(review_data.comment)

                # normalize result
                if isinstance(sentiment_result, dict):
                    sentiment_result = sentiment_result.get("label")

                if sentiment_result:
                    sentiment_result = sentiment_result.lower()

            except Exception as e:
                print("Sentiment model failed:", e)
                sentiment_result = None

        # -----------------------------
        # Create Review
        # -----------------------------
        from src.models.review import Review

        new_review = Review(
            user_id=user_id,
            place_id=review_data.place_id,
            rating=review_data.rating,
            comment=review_data.comment,
            sentiment=sentiment_result
        )

        uow.review_repository.create(new_review)

        # generate id
        uow.session.flush()

        # update place rating
        _update_place_rating_internal(uow, review_data.place_id)

        uow.commit()

        return new_review


def get_place_reviews(repo: ReviewRepository, place_id: int, page: int = 1, page_size: int = 10):

    items, total = repo.get_paginated(place_id, page, page_size)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


def get_user_reviews(repo: ReviewRepository, user_id: int, page: int = 1, page_size: int = 10):

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

        # only owner of review
        if review.user_id != current_user.id:
            raise APIException("Not authorized", code=status.HTTP_403_FORBIDDEN)

        if review_data.rating is not None:
            review.rating = review_data.rating

        # update comment and re-run sentiment
        if review_data.comment is not None and review_data.comment != review.comment:

            review.comment = review_data.comment

            try:
                sentiment_result = analyze_sentiment(review_data.comment)

                if isinstance(sentiment_result, dict):
                    sentiment_result = sentiment_result.get("label")

                review.sentiment = sentiment_result.lower()

            except Exception:
                review.sentiment = None

        _update_place_rating_internal(uow, review.place_id)

        uow.commit()

        return uow.review_repository.get_by_id(review_id)


def delete_review(uow: UnitOfWork, review_id: int, current_user: Any):

    with uow:

        review = uow.review_repository.get_by_id(review_id)

        if not review:
            raise APIException("Review not found", code=status.HTTP_404_NOT_FOUND)

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

    avg_rating, review_count = uow.review_repository.get_rating_stats(place_id)

    place = uow.place_repository.get_by_id(place_id)

    if place:
        place.rating = round(float(avg_rating), 1)
        place.review_count = int(review_count)