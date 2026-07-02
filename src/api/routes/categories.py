from fastapi import APIRouter, Depends, status
from typing import List
from src.core.dependencies import get_category_repository, get_uow, get_current_user, RoleChecker
from src.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from src.services import category_service

router = APIRouter(prefix="/categories", tags=["AI - Menu Data"])

# Admin dependencies
admin_only = RoleChecker(["ADMIN"])

@router.get("", response_model=List[CategoryResponse])
def get_categories(repo=Depends(get_category_repository)):
    """Get all main categories."""
    return category_service.get_categories(repo)

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    uow=Depends(get_uow),
    current_user=Depends(admin_only)
):
    """Admin only: Create a new main category."""
    return category_service.create_category(uow, category_in, current_user)

@router.put("/{id}", response_model=CategoryResponse)
def update_category(
    id: int,
    category_in: CategoryUpdate,
    uow=Depends(get_uow),
    current_user=Depends(admin_only)
):
    """Admin only: Update a main category."""
    return category_service.update_category(uow, id, category_in, current_user)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    id: int,
    uow=Depends(get_uow),
    current_user=Depends(admin_only)
):
    """Admin only: Delete a main category."""
    category_service.delete_category(uow, id, current_user)
    return None
