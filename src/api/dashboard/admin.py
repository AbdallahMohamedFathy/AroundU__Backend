from fastapi import APIRouter, Depends
from src.core.dependencies import get_uow
from src.schemas.user import UserResponse
from src.schemas.admin import UserPromotion, PlaceCreateWithOwner, PlaceCreationResponse, PropertyCreateWithOwner, PropertyCreationResponse
from src.services import admin_service
from src.api.dashboard.dependencies import admin_guard
from fastapi import File, UploadFile
from typing import List

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

@router.post("/properties", response_model=PropertyCreationResponse)
def create_property(
    property_in: PropertyCreateWithOwner,
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """
    Create a new property and automatically create its owner account.
    """
    return admin_service.create_property_with_owner(uow, property_in, current_user)

@router.post("/properties/{property_id}/images")
def upload_property_images(
    property_id: int,
    images: List[UploadFile] = File(...),
    uow=Depends(get_uow),
    current_user=Depends(admin_guard)
):
    """
    Upload images for an existing property (max 5 total). Requires ADMIN privilege.
    """
    return admin_service.upload_property_images(uow, property_id, images, current_user)
