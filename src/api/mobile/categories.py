from fastapi import APIRouter, Depends
from typing import List
from src.core.dependencies import get_category_repository
from src.schemas.category import CategoryResponse
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
