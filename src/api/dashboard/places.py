from fastapi import APIRouter, Depends, status
from src.core.dependencies import get_uow, get_current_user
from src.models.user import User
from src.schemas.place import PlaceCreate, PlaceUpdate, PlaceResponse
from src.services.place_service import create_place, update_place, delete_place
from src.core.permissions import require_dashboard_access
from src.core.unit_of_work import UnitOfWork

router = APIRouter(
    dependencies=[Depends(require_dashboard_access)]
)

# ─── CREATE ─────────────────────────────
@router.post("/", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
def create_new_place(
    place: PlaceCreate,
    uow: UnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    return create_place(uow, place, current_user)


# ─── UPDATE ─────────────────────────────
@router.put("/{place_id}", response_model=PlaceResponse)
def update_existing_place(
    place_id: int,
    place_data: PlaceUpdate,
    uow: UnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    return update_place(uow, place_id, place_data, current_user)


# ─── DELETE ─────────────────────────────
@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_place(
    place_id: int,
    uow: UnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    delete_place(uow, place_id, current_user)