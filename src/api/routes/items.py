from fastapi import APIRouter, Depends, status, UploadFile, File, Query
from typing import List, Optional
from src.core.dependencies import get_uow, get_current_user, RoleChecker
from src.schemas.item import ItemCreate, ItemUpdate, ItemResponse, ItemPaginationResponse
from src.services import item_service
from src.utils.file_upload import save_upload_file
from src.core.database import get_db
from src.repositories.item_repository import ItemRepository

router = APIRouter(prefix="/items", tags=["Items"])

# Owner or Admin can manage items
owner_only = RoleChecker(["OWNER", "ADMIN"])

def get_item_repo(db=Depends(get_db)):
    return ItemRepository(db)

@router.get("", response_model=ItemPaginationResponse)
def get_items(
    name: Optional[str] = Query(None),
    sub_category_id: Optional[int] = Query(None),
    place_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    repo=Depends(get_item_repo)
):
    """Get all items with search and pagination support."""
    skip = (page - 1) * size
    items, total = item_service.get_items(repo, name=name, sub_category_id=sub_category_id, place_id=place_id, skip=skip, limit=size)
    pages = (total + size - 1) // size
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/subcategory/{subcategory_id}", response_model=List[ItemResponse])
def get_items_by_subcategory(
    subcategory_id: int,
    repo=Depends(get_item_repo)
):
    """Get all items in a specific subcategory."""
    return item_service.get_items_by_subcategory(repo, subcategory_id)

@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_in: ItemCreate,
    uow=Depends(get_uow),
    current_user=Depends(owner_only)
):
    """Owner: Create a new item."""
    return item_service.create_item(uow, item_in, current_user.id, current_user.role)

@router.put("/{id}", response_model=ItemResponse)
def update_item(
    id: int,
    item_in: ItemUpdate,
    uow=Depends(get_uow),
    current_user=Depends(owner_only)
):
    """Owner: Update an item."""
    return item_service.update_item(uow, id, item_in, current_user.id, current_user.role)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    id: int,
    uow=Depends(get_uow),
    current_user=Depends(owner_only)
):
    """Owner: Delete an item (Soft delete)."""
    item_service.delete_item(uow, id, current_user.id, current_user.role)
    return None

@router.patch("/{id}/availability", response_model=ItemResponse)
def toggle_item_availability(
    id: int,
    uow=Depends(get_uow),
    current_user=Depends(owner_only)
):
    """Owner: Toggle item availability."""
    return item_service.toggle_availability(uow, id, current_user.id, current_user.role)

@router.post("/{id}/image", response_model=ItemResponse)
async def upload_item_image(
    id: int,
    file: UploadFile = File(...),
    uow=Depends(get_uow),
    current_user=Depends(owner_only)
):
    """Owner: Upload an image for an item."""
    # Save the file
    file_path = await save_upload_file(file, subfolder="items")
    
    # Update item in database
    return item_service.update_item_image(uow, id, file_path, current_user.id, current_user.role)
