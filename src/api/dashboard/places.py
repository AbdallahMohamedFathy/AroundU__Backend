from fastapi import APIRouter, Depends, status
from src.core.dependencies import get_uow, get_current_user
from src.models.user import User
from src.schemas.place import PlaceCreate, PlaceUpdate, PlaceResponse
from src.services.place_service import (
    create_place, update_place, delete_place,
)
from src.core.permissions import require_dashboard_access

router = APIRouter(dependencies=[Depends(get_current_user), Depends(require_dashboard_access)])


# ─── CREATE  POST /places ───────────────────────────────────────────────────
@router.post("/", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
def create_new_place(
    place: PlaceCreate,
    uow = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Create a new place. Requires OWNER or ADMIN."""
    return create_place(uow, place, current_user)


# ─── UPDATE  PUT /places/{id} ───────────────────────────────────────────────
@router.put("/{place_id}", response_model=PlaceResponse)
def update_existing_place(
    place_id: int,
    place_data: PlaceUpdate,
    uow = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Partially update a place. Requires owner or admin."""
    return update_place(uow, place_id, place_data, current_user)


# ─── DELETE  DELETE /places/{id} ────────────────────────────────────────────
@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_place(
    place_id: int,
    uow = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Hard-delete a place. Requires owner or admin."""
    delete_place(uow, place_id, current_user)
