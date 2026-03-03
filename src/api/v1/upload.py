from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from src.core.dependencies import get_place_image_repository, get_uow
from src.api.v1.auth import get_current_user
from src.models.user import User
from src.schemas.place_image import PlaceImageResponse
from src.utils.file_upload import save_upload_file, delete_file
from src.core.exceptions import APIException

router = APIRouter()


# ─── UPLOAD  POST /upload/place-image ───────────────────────────────────────
@router.post("/place-image", response_model=PlaceImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_place_image(
    place_id: int = Form(..., description="ID of the place this image belongs to"),
    is_primary: bool = Form(False, description="Set as the primary/cover image"),
    file: UploadFile = File(..., description="Image file (jpg, jpeg, png, gif, webp)"),
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Upload an image for a place with resilience."""
    # Save file to disk
    file_path = await save_upload_file(file, subfolder="places")
    image_url = f"/uploads/{file_path}"

    with uow:
        # If setting as primary, demote current primary
        if is_primary:
            existing_primary = uow.place_image_repository.get_primary_for_place(place_id)
            for img in existing_primary:
                img.is_primary = False

        # Create DB record
        from src.models.place_image import PlaceImage # Lazy import
        db_image = PlaceImage(
            place_id=place_id,
            image_url=image_url,
            is_primary=is_primary,
        )
        db_image = uow.place_image_repository.create(db_image)
        uow.commit()

    return db_image


# ─── LIST  GET /upload/place/{place_id}/images ──────────────────────────────
@router.get("/place/{place_id}/images")
def list_place_images(place_id: int, repo=Depends(get_place_image_repository)):
    """Return all images for a given place."""
    return repo.get_by_place(place_id)


# ─── SET PRIMARY  PUT /upload/image/{id}/primary ────────────────────────────
@router.put("/image/{image_id}/primary", response_model=PlaceImageResponse)
def set_primary_image(
    image_id: int,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Set a specific image as the primary image for its place."""
    with uow:
        image = uow.place_image_repository.get_by_id(image_id)
        if not image:
            raise APIException("Image not found", code=status.HTTP_404_NOT_FOUND)

        # Demote any current primary for this place
        existing_primary = uow.place_image_repository.get_primary_for_place(image.place_id)
        for img in existing_primary:
            img.is_primary = False

        image.is_primary = True
        uow.commit()
        return image


# ─── DELETE  DELETE /upload/image/{id} ──────────────────────────────────────
@router.delete("/image/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_place_image(
    image_id: int,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    """Delete an image record and its file from disk."""
    with uow:
        image = uow.place_image_repository.get_by_id(image_id)
        if not image:
            raise APIException("Image not found", code=status.HTTP_404_NOT_FOUND)

        # Remove from disk (strip leading /uploads/)
        relative_path = image.image_url.lstrip("/uploads/")
        delete_file(relative_path)

        uow.place_image_repository.delete(image)
        uow.commit()
