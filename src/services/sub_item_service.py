import datetime
from typing import Any
from src.models.sub_item import SubItem
from src.schemas.sub_item import SubItemCreate, SubItemUpdate
from src.core.exceptions import APIException
from fastapi import status


def _get_item_and_check_permission(uow: Any, item_id: int, user_id: int, user_role: str):
    item = uow.item_repository.get_by_id(item_id)
    if not item or item.is_deleted:
        raise APIException("Item not found", code=status.HTTP_404_NOT_FOUND)

    subcategory = uow.subcategory_repository.get_by_id(item.sub_category_id)
    if not subcategory or subcategory.is_deleted:
        raise APIException("SubCategory not found", code=status.HTTP_404_NOT_FOUND)

    if user_role != "ADMIN" and subcategory.owner_id != user_id:
        raise APIException("You don't have permission to manage sub-items for this item", code=status.HTTP_403_FORBIDDEN)

    return item


def create_sub_item(uow: Any, item_id: int, sub_item_in: SubItemCreate, user_id: int, user_role: str):
    with uow:
        _get_item_and_check_permission(uow, item_id, user_id, user_role)

        existing = uow.sub_item_repository.get_by_name_and_item(sub_item_in.name, item_id)
        if existing:
            raise APIException("A sub-item with this name already exists for this item", code=status.HTTP_400_BAD_REQUEST)

        db_sub_item = SubItem(
            name=sub_item_in.name,
            description=sub_item_in.description,
            price=sub_item_in.price,
            is_available=sub_item_in.is_available,
            item_id=item_id,
        )
        uow.sub_item_repository.create(db_sub_item)
        uow.commit()
        return uow.sub_item_repository.get_by_id(db_sub_item.id)


def update_sub_item(uow: Any, sub_item_id: int, sub_item_in: SubItemUpdate, user_id: int, user_role: str):
    with uow:
        db_sub_item = uow.sub_item_repository.get_by_id(sub_item_id)
        if not db_sub_item:
            raise APIException("Sub-item not found", code=status.HTTP_404_NOT_FOUND)

        _get_item_and_check_permission(uow, db_sub_item.item_id, user_id, user_role)

        if sub_item_in.name and sub_item_in.name != db_sub_item.name:
            existing = uow.sub_item_repository.get_by_name_and_item(sub_item_in.name, db_sub_item.item_id)
            if existing:
                raise APIException("A sub-item with this name already exists for this item", code=status.HTTP_400_BAD_REQUEST)

        update_data = sub_item_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_sub_item, field, value)

        uow.session.flush()
        uow.session.refresh(db_sub_item)
        uow.commit()
        return uow.sub_item_repository.get_by_id(db_sub_item.id)


def delete_sub_item(uow: Any, sub_item_id: int, user_id: int, user_role: str):
    with uow:
        db_sub_item = uow.sub_item_repository.get_by_id(sub_item_id)
        if not db_sub_item:
            raise APIException("Sub-item not found", code=status.HTTP_404_NOT_FOUND)

        _get_item_and_check_permission(uow, db_sub_item.item_id, user_id, user_role)

        db_sub_item.is_deleted = True
        db_sub_item.deleted_at = datetime.datetime.now(datetime.timezone.utc)
        uow.commit()
        return True


def toggle_sub_item_availability(uow: Any, sub_item_id: int, user_id: int, user_role: str):
    with uow:
        db_sub_item = uow.sub_item_repository.get_by_id(sub_item_id)
        if not db_sub_item:
            raise APIException("Sub-item not found", code=status.HTTP_404_NOT_FOUND)

        _get_item_and_check_permission(uow, db_sub_item.item_id, user_id, user_role)

        db_sub_item.is_available = not db_sub_item.is_available
        uow.commit()
        return uow.sub_item_repository.get_by_id(db_sub_item.id)
