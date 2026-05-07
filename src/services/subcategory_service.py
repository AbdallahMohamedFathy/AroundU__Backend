from typing import List, Optional, Any
from src.core.unit_of_work import UnitOfWork
from src.repositories.subcategory_repository import SubCategoryRepository
from src.schemas.subcategory import SubCategoryCreate, SubCategoryUpdate
from src.core.exceptions import APIException
from src.models.subcategory import SubCategory
from fastapi import status
import datetime

def get_subcategories_by_place(repo: SubCategoryRepository, place_id: int):
    return repo.get_by_place(place_id)

def get_owner_subcategories(repo: SubCategoryRepository, owner_id: int):
    return repo.get_by_owner(owner_id)

def create_subcategory(uow: UnitOfWork, subcategory_in: SubCategoryCreate, owner_id: int):
    with uow:
        # Check if place exists and belongs to owner
        place = uow.place_repository.get_by_id(subcategory_in.place_id)
        if not place:
            raise APIException("Place not found", code=status.HTTP_404_NOT_FOUND)
        
        if place.owner_id != owner_id:
            raise APIException("You don't have permission to add subcategories to this place", code=status.HTTP_403_FORBIDDEN)

        # Prevent duplicate subcategory names for same owner
        existing = uow.subcategory_repository.get_by_name_and_owner(subcategory_in.name, owner_id)
        if existing:
            raise APIException("SubCategory with this name already exists for this owner", code=status.HTTP_400_BAD_REQUEST)

        db_subcategory = SubCategory(
            **subcategory_in.model_dump(),
            owner_id=owner_id
        )
        uow.subcategory_repository.create(db_subcategory)
        uow.commit()
        return db_subcategory

def update_subcategory(uow: UnitOfWork, subcategory_id: int, subcategory_in: SubCategoryUpdate, owner_id: int):
    with uow:
        subcategory = uow.subcategory_repository.get_by_id(subcategory_id)
        if not subcategory or subcategory.is_deleted:
            raise APIException("SubCategory not found", code=status.HTTP_404_NOT_FOUND)

        if subcategory.owner_id != owner_id:
            raise APIException("You don't have permission to update this subcategory", code=status.HTTP_403_FORBIDDEN)

        if subcategory_in.name and subcategory_in.name != subcategory.name:
            existing = uow.subcategory_repository.get_by_name_and_owner(subcategory_in.name, owner_id)
            if existing:
                raise APIException("SubCategory with this name already exists for this owner", code=status.HTTP_400_BAD_REQUEST)

        update_data = subcategory_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subcategory, field, value)
        
        uow.commit()
        return subcategory

def delete_subcategory(uow: UnitOfWork, subcategory_id: int, owner_id: int):
    with uow:
        subcategory = uow.subcategory_repository.get_by_id(subcategory_id)
        if not subcategory or subcategory.is_deleted:
            raise APIException("SubCategory not found", code=status.HTTP_404_NOT_FOUND)

        if subcategory.owner_id != owner_id:
            raise APIException("You don't have permission to delete this subcategory", code=status.HTTP_403_FORBIDDEN)

        # Soft delete
        subcategory.is_deleted = True
        subcategory.deleted_at = datetime.datetime.now(datetime.timezone.utc)
        uow.commit()
        return True

def update_subcategory_image(uow: UnitOfWork, subcategory_id: int, image_url: str, owner_id: int):
    with uow:
        subcategory = uow.subcategory_repository.get_by_id(subcategory_id)
        if not subcategory or subcategory.is_deleted:
            raise APIException("SubCategory not found", code=status.HTTP_404_NOT_FOUND)

        if subcategory.owner_id != owner_id:
            raise APIException("You don't have permission to update this subcategory", code=status.HTTP_403_FORBIDDEN)

        subcategory.image_url = image_url
        uow.commit()
        return subcategory
