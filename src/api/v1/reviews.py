from fastapi import APIRouter, Depends, Query, status
from src.core.dependencies import get_review_repository, get_uow
from src.api.v1.auth import get_current_user
from src.models.user import User
from src.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse
from src.services import review_service

router = APIRouter()


# ─── LIST FOR PLACE  GET /reviews/place/{id} ────────────────────────────────
@router.get("/place/{place_id}")
def list_place_reviews(
    place_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    repo=Depends(get_review_repository),
):
    """Return all reviews for a given place (public)."""
    return review_service.get_place_reviews(repo, place_id, page, page_size)


# ─── LIST MINE  GET /reviews/me ─────────────────────────────────────────────
@router.get("/me")
def list_my_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    repo=Depends(get_review_repository),
    current_user: User = Depends(get_current_user),
):
    """Return all reviews written by the current user."""
    return review_service.get_user_reviews(repo, current_user.id, page, page_size)


# ─── GET ONE  GET /reviews/{id} ─────────────────────────────────────────────
@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, repo=Depends(get_review_repository)):
    """Retrieve a single review by ID."""
    return review_service.get_review_by_id(repo, review_id)


# ─── CREATE  POST /reviews ───────────────────────────────────────────────────
@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_place_review(
    data: ReviewCreate,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Create a review for a place. Each user can review a place only once."""
    return review_service.create_review(uow, current_user.id, data)


# ─── UPDATE  PUT /reviews/{id} ──────────────────────────────────────────────
@router.put("/{review_id}", response_model=ReviewResponse)
def update_place_review(
    review_id: int,
    data: ReviewUpdate,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Update your own review (rating and/or comment)."""
    return review_service.update_review(uow, review_id, current_user.id, data)


# ─── DELETE  DELETE /reviews/{id} ───────────────────────────────────────────
@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_place_review(
    review_id: int,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Delete your own review."""
    review_service.delete_review(uow, review_id, current_user.id)
