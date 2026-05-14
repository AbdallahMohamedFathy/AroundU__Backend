from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from src.api.dashboard.dependencies import owner_guard
from app.dependencies import get_db
from app.orders.services.order_service import OrderService
from app.orders.schemas.order import OrderResponse
from app.auth import get_current_user

router = APIRouter(tags=["Dashboard - Owner"])


@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="Get My Orders (All Branches)",
    description=(
        "Owner receives all orders across **all their places (branches)**.\n\n"
        "Filters orders by joining with the `places` table where `place.owner_id = current_user.id`."
    ),
)
async def get_owner_orders(
    db=Depends(get_db),
    current_user=Depends(owner_guard),
):
    user_role = str(getattr(current_user, "role", "")).upper()
    if user_role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Owner access required (current role: {user_role})"
        )

    service = OrderService(db)
    # Uses JOIN: Order → Place WHERE Place.owner_id = current_user.id
    orders = await service.order_repo.get_owner_orders(current_user.id)

    result = []
    for o in orders:
        items_res = [
            {
                "id": i.id,
                "item_id": i.item_id,
                "item_name": i.item_name,
                "image_url": i.image_url,
                "unit_price": i.unit_price,
                "quantity": i.quantity,
                "total_price": i.total_price,
            }
            for i in getattr(o, 'items', [])
        ]
        result.append(OrderResponse(
            id=o.id,
            user_id=o.user_id,
            place_id=o.place_id,
            order_type=o.order_type,
            status=o.status,
            full_name=o.full_name,
            phone_number=o.phone_number,
            address=o.address,
            notes=o.notes,
            total_price=o.total_price,
            items=items_res,
            created_at=o.created_at,
        ))
    return result


@router.get(
    "/place/{place_id}",
    response_model=List[OrderResponse],
    summary="Get Orders by Branch",
    description=(
        "Owner receives orders for a **specific place (branch)**.\n\n"
        "Useful for multi-branch owners who want to filter per location."
    ),
)
async def get_place_orders(
    place_id: int,
    db=Depends(get_db),
    current_user=Depends(owner_guard),
):
    user_role = str(getattr(current_user, "role", "")).upper()
    if user_role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Owner access required (current role: {user_role})"
        )

    service = OrderService(db)
    orders = await service.order_repo.get_place_orders(place_id)

    result = []
    for o in orders:
        items_res = [
            {
                "id": i.id,
                "item_id": i.item_id,
                "item_name": i.item_name,
                "image_url": i.image_url,
                "unit_price": i.unit_price,
                "quantity": i.quantity,
                "total_price": i.total_price,
            }
            for i in getattr(o, 'items', [])
        ]
        result.append(OrderResponse(
            id=o.id,
            user_id=o.user_id,
            place_id=o.place_id,
            order_type=o.order_type,
            status=o.status,
            full_name=o.full_name,
            phone_number=o.phone_number,
            address=o.address,
            notes=o.notes,
            total_price=o.total_price,
            items=items_res,
            created_at=o.created_at,
        ))
    return result


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update Order Status",
    description="Owner accepts, rejects, or advances the status of an order for their place.",
)
async def update_order_status(
    order_id: int,
    new_status: str,
    db=Depends(get_db),
    current_user=Depends(owner_guard),
):
    user_role = str(getattr(current_user, "role", "")).upper()
    if user_role != "OWNER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Owner access required (current role: {user_role})"
        )

    from app.orders.enums.enums import OrderStatus
    service = OrderService(db)
    return await service.change_status(order_id=order_id, new_status=OrderStatus(new_status), actor="owner")
