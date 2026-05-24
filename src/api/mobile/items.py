from fastapi import APIRouter, Depends, Query
from typing import List
from src.core.dependencies import get_uow
from src.services import item_service
from src.core.unit_of_work import UnitOfWork
from src.schemas.item import ItemResponse

router = APIRouter()

@router.get("/place/{place_id}", response_model=List[ItemResponse])
def list_place_items(
    place_id: int,
    uow: UnitOfWork = Depends(get_uow)
):
    with uow:
        return item_service.get_items_by_place(
            repo=uow.item_repository,
            place_id=place_id
        )

@router.get(
    "/place/{place_id}/top",
    response_model=List[ItemResponse],
    summary="Get top items for a place",
    description=(
        "Returns the top available items for a given place (or branch). "
        "Works for both parent places and branches — pass the specific place_id. "
        "Items are ordered by newest first."
    ),
)
def get_top_place_items(
    place_id: int,
    limit: int = Query(4, ge=1, le=20, description="Number of top items to return"),
    uow: UnitOfWork = Depends(get_uow),
):
    with uow:
        return item_service.get_top_items_by_place(
            repo=uow.item_repository,
            place_id=place_id,
            limit=limit,
        )