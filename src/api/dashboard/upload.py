from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from src.core.dependencies import get_current_user, get_uow, get_place_image_repository
from src.models.user import User
from src.schemas.place_image import PlaceImageResponse
from src.utils.file_upload import save_upload_file, delete_file
from src.core.exceptions import APIException
from src.core.permissions import require_place_owner_or_admin
from src.api.dashboard.dependencies import dashboard_guard

router = APIRouter(
    dependencies=[Depends(dashboard_guard)]
)

# ─── UPLOAD ─────────────────────────────
@router.post("/place-image", response_model=PlaceImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_place_image(
    place_id: int = Form(...),
    image_type: str = Form(...), # 'place' or 'menu'
    caption: Optional[str] = Form(None),
    file: UploadFile = File(...),
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    with uow:
        place = uow.place_repository.get_by_id(place_id)
        if not place:
            raise APIException("Place not found", code=status.HTTP_404_NOT_FOUND)

        require_place_owner_or_admin(current_user, place)

    file_path = await save_upload_file(file, subfolder="places")
    # In a real external storage scenario, this would be a Cloudinary/S3 URL
    # For now, we use the local /uploads/ URL
    image_url = f"/uploads/{file_path}"

    with uow:
        from src.models.place_image import PlaceImage
        db_image = PlaceImage(
            place_id=place_id,
            image_url=image_url,
            image_type=image_type,
            caption=caption
        )

        db_image = uow.place_image_repository.create(db_image)
        uow.commit()

    return db_image


# ─── LIST ─────────────────────────────
@router.get("/place/{place_id}/images")
def list_place_images(
    place_id: int,
    repo=Depends(get_place_image_repository)
):
    return repo.get_by_place(place_id)




# ─── DELETE ─────────────────────────────
@router.delete("/image/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_place_image(
    image_id: int,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user),
):
    with uow:
        image = uow.place_image_repository.get_by_id(image_id)
        if not image:
            raise APIException("Image not found", code=status.HTTP_404_NOT_FOUND)

        place = uow.place_repository.get_by_id(image.place_id)
        require_place_owner_or_admin(current_user, place)

        relative_path = image.image_url.lstrip("/uploads/")
        delete_file(relative_path)

        uow.place_image_repository.delete(image)
        uow.commit()