from fastapi import APIRouter, Depends, status
from src.core.dependencies import get_uow, get_current_user
from src.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from src.services import item_service
from src.models.user import User
from src.api.dashboard.dependencies import dashboard_guard
from src.core.unit_of_work import UnitOfWork

router = APIRouter(
    dependencies=[Depends(dashboard_guard)]
)

@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_new_item(
    item_in: ItemCreate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    """Dashboard: Create a new item."""
    return item_service.create_item(
        uow=uow,
        item_in=item_in,
        user_id=current_user.id,
        user_role=current_user.role
    )


@router.put("/{item_id}", response_model=ItemResponse)
def update_existing_item(
    item_id: int,
    item_in: ItemUpdate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    """Dashboard: Update an item."""
    return item_service.update_item(
        uow=uow,
        item_id=item_id,
        item_in=item_in,
        user_id=current_user.id,
        user_role=current_user.role
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    """Dashboard: Delete an item."""
    item_service.delete_item(
        uow=uow,
        item_id=item_id,
        user_id=current_user.id,
        user_role=current_user.role
    )
    return None

from fastapi import UploadFile, File
from src.utils.file_upload import save_upload_file

@router.post("/{item_id}/image", response_model=ItemResponse)
async def upload_item_image(
    item_id: int,
    file: UploadFile = File(...),
    uow: UnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user)
):
    """Dashboard: Upload an image for an item."""
    # Save the file
    file_path = await save_upload_file(file, subfolder="items")
    
    # Update item in database
    return item_service.update_item_image(uow, item_id, file_path, current_user.id, current_user.role)