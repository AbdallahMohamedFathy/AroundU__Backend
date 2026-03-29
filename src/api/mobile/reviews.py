from fastapi import APIRouter, Depends, Query, status, HTTPException
from src.core.dependencies import get_review_repository, get_uow, get_current_user
from src.models.user import User
from src.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse, ReviewListResponse, ReviewWithUser
from src.services import review_service

router = APIRouter()


# ─── LIST FOR PLACE  GET /reviews/place/{id} ────────────────────────────────
@router.get("/place", response_model=ReviewListResponse)
def list_place_reviews(
    place_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    repo=Depends(get_review_repository),
):
    """Return reviews using query parameter (?place_id=9)"""
    if not place_id:
        raise HTTPException(status_code=422, detail="place_id is required")
    return review_service.get_place_reviews(repo, place_id, page, page_size)


@router.get("/place/{place_id}", response_model=ReviewListResponse)
def list_place_reviews_by_path(
    place_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    repo=Depends(get_review_repository),
):
    """Return reviews using path parameter (/place/9)"""
    if not place_id:
        raise HTTPException(status_code=422, detail="place_id is required")
    return review_service.get_place_reviews(repo, place_id, page, page_size)


# ─── LIST MINE  GET /reviews/me ─────────────────────────────────────────────
@router.get("/me", response_model=ReviewListResponse)
def list_my_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    repo=Depends(get_review_repository),
    current_user: User = Depends(get_current_user),
):
    """Return all reviews written by the current user."""
    return review_service.get_user_reviews(repo, current_user.id, page, page_size)


# ─── GET ONE  GET /reviews/{id} ─────────────────────────────────────────────
@router.get("/{review_id}", response_model=ReviewWithUser)
def get_review(review_id: int, repo=Depends(get_review_repository)):
    """Retrieve a single review by ID."""
    return review_service.get_review_by_id(repo, review_id)


# ─── CREATE  POST /reviews ───────────────────────────────────────────────────
@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_place_review(
    data: ReviewCreate,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Create a review for a place. Each user can review a place only once."""
    return await review_service.create_review(uow, current_user.id, data)


# ─── UPDATE  PUT /reviews/{id} ──────────────────────────────────────────────
@router.put("/{review_id}", response_model=ReviewResponse)
async def update_place_review(
    review_id: int,
    data: ReviewUpdate,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Update your own review (rating and/or comment)."""
    return await review_service.update_review(uow, review_id, current_user, data)


# ─── DELETE  DELETE /reviews/{id} ───────────────────────────────────────────
@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_place_review(
    review_id: int,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Delete a review. Authorized for reviewer, place owner, or admin."""
    review_service.delete_review(uow, review_id, current_user)
