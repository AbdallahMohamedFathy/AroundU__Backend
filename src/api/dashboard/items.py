from fastapi import APIRouter, Depends, status, Query
from typing import List
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

@router.get("/place/{place_id}/top", response_model=List[ItemResponse])
def get_top_place_items(
    place_id: int,
    limit: int = Query(10, ge=1, le=50),
    uow: UnitOfWork = Depends(get_uow),
):
    """Dashboard: Get best-selling items for a place ordered by most ordered."""
    with uow:
        return item_service.get_top_items_by_place(
            repo=uow.item_repository,
            place_id=place_id,
            limit=limit,
        )


from fastapi import UploadFile, File
from src.services.cloudinary_service import upload_image, delete_image

@router.post("/{item_id}/image", response_model=ItemResponse)
async def upload_item_image(
    item_id: int,
    file: UploadFile = File(...),
    uow: UnitOfWork = Depends(get_uow),
    current_user: User = Depends(get_current_user)
):
    """Dashboard: Upload an image for an item."""
    # 1. Fetch item to check permissions and get old image URL
    with uow:
        db_item = uow.item_repository.get_by_id(item_id)
        if not db_item or db_item.is_deleted:
            from src.core.exceptions import APIException
            raise APIException("Item not found", code=status.HTTP_404_NOT_FOUND)
            
        # Permission check via subcategory
        subcategory = uow.subcategory_repository.get_by_id(db_item.sub_category_id)
        if current_user.role != "ADMIN" and subcategory.owner_id != current_user.id:
            from src.core.exceptions import APIException
            raise APIException("You don't have permission to update this item", code=status.HTTP_403_FORBIDDEN)
            
        old_image_url = db_item.image_url

    # 2. Upload new image to Cloudinary
    new_image_url = upload_image(file, folder="items")
    
    # 3. Delete old image from Cloudinary if it exists
    if old_image_url:
        delete_image(old_image_url)
    
    # 4. Update item in database
    return item_service.update_item_image(uow, item_id, new_image_url, current_user.id, current_user.role)