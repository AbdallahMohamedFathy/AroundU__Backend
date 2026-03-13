from fastapi import APIRouter, Depends
from src.core.dependencies import get_uow
from src.schemas.user import UserResponse
from src.schemas.admin import UserPromotion, PlaceCreateWithOwner, PlaceCreationResponse
from src.services import admin_service
from src.api.dashboard.dependencies import admin_guard

router = APIRouter(dependencies=[Depends(admin_guard)])

@router.post("/promote/{user_id}", response_model=UserResponse)
def promote_user(
    user_id: int,
    promotion: UserPromotion,
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """
    Change a user's role. Requires ADMIN privilege.
    """
    return admin_service.promote_user(uow, user_id, promotion.role, current_user)

@router.post("/places", response_model=PlaceCreationResponse)
def create_place(
    place_in: PlaceCreateWithOwner,
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """
    Create a new place and automatically create its owner account.
    """
    return admin_service.create_place_with_owner(uow, place_in, current_user)
