from typing import List, Optional, Any
from fastapi import UploadFile, HTTPException, status
from src.models.property import Property
from src.models.property_image import PropertyImage
from src.models.property_review import PropertyReview
from src.schemas.property import PropertyCreate, PropertyUpdate, PropertyReviewCreate
from src.services.cloudinary_service import upload_image, delete_image
from src.core.exceptions import APIException
from src.core.logger import logger
import math

def create_property_review(repo: Any, property_id: int, review_data: PropertyReviewCreate, current_user: Any):
    db_prop = repo.get_by_id(property_id)
    if not db_prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    # Optional: Check if user already reviewed (one review per property)
    existing = repo.session.query(PropertyReview).filter(
        PropertyReview.property_id == property_id,
        PropertyReview.user_id == current_user.id
    ).first()
    if existing:
        raise APIException("You have already reviewed this property", code=status.HTTP_400_BAD_REQUEST)

    db_review = PropertyReview(
        property_id=property_id,
        user_id=current_user.id,
        rating=review_data.rating,
        comment=review_data.comment
    )
    repo.session.add(db_review)
    repo.session.commit()
    repo.session.refresh(db_review)
    return db_review



MAX_IMAGES = 5
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

def validate_image(file: UploadFile):
    extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise APIException(
            f"Invalid file type: {extension}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            code=status.HTTP_400_BAD_REQUEST
        )

def get_properties(
    repo: Any,
    page: int = 1,
    limit: int = 20,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = "newest"
):
    items, total = repo.get_paginated_filtered(
        page=page,
        page_size=limit,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by
    )
    
    return {
        "total": total,
        "page": page,
        "page_size": limit,
        "total_pages": math.ceil(total / limit) if total else 0,
        "items": items
    }

def get_my_properties(repo: Any, current_user: Any):
    return repo.get_my_properties(current_user.id)

def get_property_by_id(repo: Any, property_id: int):
    prop = repo.get_by_id_with_images(property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return prop

def create_property(repo: Any, property_data: PropertyCreate, images: List[UploadFile], current_user: Any):
    if len(images) > MAX_IMAGES:
        raise APIException(f"Maximum {MAX_IMAGES} images allowed", code=status.HTTP_400_BAD_REQUEST)

    # 1. Upload images
    image_urls = []
    for image in images:
        validate_image(image)
        url = upload_image(image, folder="properties")
        image_urls.append(url)

    # 2. Create property
    main_image = image_urls[0] if image_urls else None
    
    db_property = Property(
        **property_data.model_dump(),
        owner_id=current_user.id,
        main_image_url=main_image
    )
    
    db_property = repo.create(db_property)

    # 3. Create property images
    for url in image_urls:
        img = PropertyImage(property_id=db_property.id, image_url=url)
        repo.session.add(img)
    
    repo.session.commit()
    repo.session.refresh(db_property)
    return db_property

def update_property(repo: Any, property_id: int, property_data: PropertyUpdate, new_images: List[UploadFile], current_user: Any):
    db_prop = repo.get_by_id_with_images(property_id)
    if not db_prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    if db_prop.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this property")

    # 1. Handle basic field updates
    update_dict = property_data.model_dump(exclude_unset=True, exclude={"image_ids_to_delete"})
    for key, value in update_dict.items():
        setattr(db_prop, key, value)

    # 2. Handle image deletions
    if property_data.image_ids_to_delete:
        for img_id in property_data.image_ids_to_delete:
            img = next((i for i in db_prop.images if i.id == img_id), None)
            if img:
                # Delete from Cloudinary
                delete_image(img.image_url)
                # Remove from DB
                repo.session.delete(img)
        repo.session.flush() # Ensure deletions are reflected for limit check

    # 3. Handle new image uploads
    current_image_count = len(db_prop.images)
    if current_image_count + len(new_images) > MAX_IMAGES:
        raise APIException(f"Total images cannot exceed {MAX_IMAGES}", code=status.HTTP_400_BAD_REQUEST)

    for image in new_images:
        validate_image(image)
        url = upload_image(image, folder="properties")
        new_img = PropertyImage(property_id=db_prop.id, image_url=url)
        repo.session.add(new_img)
        
        # If no main image exists, set it
        if not db_prop.main_image_url:
            db_prop.main_image_url = url

    repo.session.commit()
    repo.session.refresh(db_prop)
    return db_prop

def delete_property(repo: Any, property_id: int, current_user: Any):
    db_prop = repo.get_by_id_with_images(property_id)
    if not db_prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    if db_prop.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this property")

    # Clean up Cloudinary images
    for img in db_prop.images:
        delete_image(img.image_url)
    
    if db_prop.main_image_url:
        delete_image(db_prop.main_image_url)

    repo.delete(db_prop)
    repo.session.commit()
