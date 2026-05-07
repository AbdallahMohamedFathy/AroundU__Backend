from fastapi import APIRouter, Depends, status, UploadFile, File
from typing import List
from src.core.dependencies import get_uow, get_current_user, RoleChecker
from src.schemas.subcategory import SubCategoryCreate, SubCategoryUpdate, SubCategoryResponse
from src.services import subcategory_service
from src.utils.file_upload import save_upload_file
from src.core.database import get_db
from src.repositories.subcategory_repository import SubCategoryRepository

router = APIRouter(prefix="/subcategories", tags=["SubCategories"])

# Owner or Admin can manage subcategories (Owner manages his own)
owner_only = RoleChecker(["OWNER", "ADMIN"])

def get_subcategory_repo(db=Depends(get_db)):
    return SubCategoryRepository(db)

@router.get("/category/{category_id}", response_model=List[SubCategoryResponse])
def get_subcategories_by_category(
    category_id: int,
    repo=Depends(get_subcategory_repo)
):
    """Get all subcategories belonging to a specific main category."""
    return subcategory_service.get_subcategories_by_category(repo, category_id)

@router.get("/my", response_model=List[SubCategoryResponse])
def get_my_subcategories(
    current_user=Depends(get_current_user),
    repo=Depends(get_subcategory_repo)
):
    """Get all subcategories owned by the current owner."""
    return subcategory_service.get_owner_subcategories(repo, current_user.id)

@router.post("", response_model=SubCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_subcategory(
    subcategory_in: SubCategoryCreate,
    uow=Depends(get_uow),
    current_user=Depends(owner_only)
):
    """Owner: Create a new subcategory."""
    return subcategory_service.create_subcategory(uow, subcategory_in, current_user.id)

@router.put("/{id}", response_model=SubCategoryResponse)
def update_subcategory(
    id: int,
    subcategory_in: SubCategoryUpdate,
    uow=Depends(get_uow),
    current_user=Depends(owner_only)
):
    """Owner: Update a subcategory."""
    return subcategory_service.update_subcategory(uow, id, subcategory_in, current_user.id)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subcategory(
    id: int,
    uow=Depends(get_uow),
    current_user=Depends(owner_only)
):
    """Owner: Delete a subcategory (Soft delete)."""
    subcategory_service.delete_subcategory(uow, id, current_user.id)
    return None

from src.utils.file_upload import save_upload_file

@router.post("/{id}/image", response_model=SubCategoryResponse)
async def upload_subcategory_image(
    id: int,
    file: UploadFile = File(...),
    uow=Depends(get_uow),
    current_user=Depends(owner_only)
):
    """Owner: Upload an image for a subcategory."""
    # Save the file
    file_path = await save_upload_file(file, subfolder="subcategories")
    
    # Update subcategory in database
    return subcategory_service.update_subcategory_image(uow, id, file_path, current_user.id)
