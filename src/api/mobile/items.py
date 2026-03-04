from fastapi import APIRouter, Depends
from src.core.dependencies import get_uow
from src.services import item_service
from src.core.unit_of_work import UnitOfWork

router = APIRouter()

@router.get("/place/{place_id}")
def list_place_items(
    place_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    with uow:
        return item_service.get_items_by_place(
            repo=uow.item_repository,
            place_id=place_id
        )