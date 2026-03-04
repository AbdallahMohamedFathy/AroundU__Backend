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

@router.post("/place/{place_id}", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_new_item(
    place_id: int,
    item_in: ItemCreate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    return item_service.create_item(
        uow=uow,
        place_id=place_id,
        item_in=item_in,
        current_user=current_user
    )


@router.put("/{item_id}", response_model=ItemResponse)
def update_existing_item(
    item_id: int,
    item_in: ItemUpdate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    return item_service.update_item(
        uow=uow,
        item_id=item_id,
        item_in=item_in,
        current_user=current_user
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    item_service.delete_item(
        uow=uow,
        item_id=item_id,
        current_user=current_user
    )