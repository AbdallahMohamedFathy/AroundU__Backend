from fastapi import APIRouter, Depends, status
from typing import List
from src.core.dependencies import get_category_repository, get_uow
from src.api.v1.auth import get_current_user
from src.models.user import User
from src.schemas.category import CategoryBase, CategoryResponse
from src.services import category_service

router = APIRouter()


# ─── LIST  GET /categories ──────────────────────────────────────────────────
@router.get("/", response_model=List[CategoryResponse])
def list_categories(
    skip: int = 0, 
    limit: int = 100, 
    repo=Depends(get_category_repository)
):
    """Return all categories."""
    return category_service.get_categories(repo, skip=skip, limit=limit)


# ─── GET ONE  GET /categories/{id} ─────────────────────────────────────────
@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, repo=Depends(get_category_repository)):
    """Retrieve a single category by ID."""
    return category_service.get_category_by_id(repo, category_id)


# ─── CREATE  POST /categories ───────────────────────────────────────────────
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_new_category(
    category: CategoryBase,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Create a new category. Requires authentication."""
    return category_service.create_category(uow, category)


# ─── UPDATE  PUT /categories/{id} ───────────────────────────────────────────
@router.put("/{category_id}", response_model=CategoryResponse)
def update_existing_category(
    category_id: int,
    category_data: CategoryBase,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Update a category. Requires authentication."""
    return category_service.update_category(uow, category_id, category_data)


# ─── DELETE  DELETE /categories/{id} ────────────────────────────────────────
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_category(
    category_id: int,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Delete a category. Requires authentication."""
    category_service.delete_category(uow, category_id)
