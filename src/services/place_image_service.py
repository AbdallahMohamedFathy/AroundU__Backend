from typing import List, Any
from fastapi import status
from src.models.place_image import PlaceImage
from src.schemas.place_image import PlaceImageCreate, PlaceImageResponse
from src.core.exceptions import APIException
from src.core.permissions import require_place_owner_or_admin

def get_place_images(repo: Any, place_id: int) -> List[PlaceImage]:
    """Return all images for a specific place."""
    return repo.get_by_place(place_id)

def add_place_image(uow: Any, place_id: int, image_data: PlaceImageCreate, current_user: Any):
    """Add a new image to a place."""
    with uow as uow:
        place = uow.place_repository.get_by_id(place_id)
        if not place:
            raise APIException("Place not found", code=status.HTTP_404_NOT_FOUND)
        
        require_place_owner_or_admin(current_user, place)
        
        db_image = PlaceImage(
            place_id=place_id,
            image_url=image_data.image_url,
            image_type=image_data.image_type,
            caption=image_data.caption
        )
        
        db_image = uow.place_image_repository.create(db_image)
        uow.commit()
        return PlaceImageResponse.model_validate(db_image)

def delete_place_image(uow: Any, image_id: int, current_user: Any):
    """Delete an image If the user is owner or admin."""
    with uow as uow:
        image = uow.place_image_repository.get_by_id(image_id)
        if not image:
            raise APIException("Image not found", code=status.HTTP_404_NOT_FOUND)
        
        place = uow.place_repository.get_by_id(image.place_id)
        require_place_owner_or_admin(current_user, place)
        
        uow.place_image_repository.delete(image)
        uow.commit()
