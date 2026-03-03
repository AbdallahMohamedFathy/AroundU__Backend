from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.core.dependencies import get_db, get_current_user
from src.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from src.services.item_service import ItemService
from src.models.user import User
from src.core.permissions import require_dashboard_access

router = APIRouter(
    dependencies=[Depends(require_dashboard_access)]
)

@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    place_id: int,
    item_in: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = ItemService(db)
    return service.create_item(place_id=place_id, item_in=item_in, current_user=current_user)


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item_in: ItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = ItemService(db)
    return service.update_item(item_id=item_id, item_in=item_in, current_user=current_user)


@router.delete("/{item_id}", response_model=ItemResponse)
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = ItemService(db)
    return service.delete_item(item_id=item_id, current_user=current_user)