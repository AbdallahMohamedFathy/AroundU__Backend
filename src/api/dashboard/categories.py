from fastapi import APIRouter, Depends, status
from src.core.dependencies import get_uow
from src.models.user import User
from src.schemas.category import CategoryBase, CategoryResponse
from src.services import category_service
from src.api.dashboard.dependencies import admin_guard

router = APIRouter(dependencies=[Depends(admin_guard)])


# ─── CREATE  POST /categories ───────────────────────────────────────────────
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_new_category(
    category: CategoryBase,
    uow=Depends(get_uow),
    current_user: User = Depends(admin_guard),
):
    """Create a new category. Requires ADMIN role."""
    return category_service.create_category(uow, category, current_user)


# ─── UPDATE  PUT /categories/{id} ───────────────────────────────────────────
@router.put("/{category_id}", response_model=CategoryResponse)
def update_existing_category(
    category_id: int,
    category_data: CategoryBase,
    uow=Depends(get_uow),
    current_user: User = Depends(admin_guard),
):
    """Update a category. Requires ADMIN role."""
    return category_service.update_category(uow, category_id, category_data, current_user)


# ─── DELETE  DELETE /categories/{id} ────────────────────────────────────────
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_category(
    category_id: int,
    uow=Depends(get_uow),
    current_user: User = Depends(admin_guard),
):
    """Delete a category. Requires ADMIN role."""
    category_service.delete_category(uow, category_id, current_user)
