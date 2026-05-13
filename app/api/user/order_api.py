from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.dependencies import get_db
from app.orders.services.order_service import OrderService
from app.orders.schemas.order import OrderCreate, OrderResponse
from app.orders.enums.enums import OrderStatus
from app.auth import get_current_user

# Group all user order endpoints under the "Mobile - Orders" tag
router = APIRouter(tags=["Mobile - Orders"])


@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout Order",
    description=(
        "Create a new order for the authenticated user.\n\n"
        "Only **place_id** is required — the system routes the order to the correct place (branch) automatically.\n\n"
        "Business rule: all items in the request must belong to the same `place_id`."
    ),
)
async def checkout_order(
    order_data: OrderCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = OrderService(db)
    return await service.checkout(user_id=current_user.id, order_data=order_data)


@router.get(
    "/my",
    response_model=List[OrderResponse],
    summary="Get My Orders",
    description="Retrieve all orders placed by the authenticated user.",
)
async def get_my_orders(
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = OrderService(db)
    orders = await service.order_repo.get_user_orders(current_user.id)
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
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get Order Details",
    description="Get full details (including items) of a specific order — **user can only access their own orders**.",
)
async def get_order(
    order_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = OrderService(db)
    order = await service.order_repo.get_order(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

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
        for i in order.items
    ]
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        place_id=order.place_id,
        order_type=order.order_type,
        status=order.status,
        full_name=order.full_name,
        phone_number=order.phone_number,
        address=order.address,
        notes=order.notes,
        total_price=order.total_price,
        items=items_res,
        created_at=order.created_at,
    )


@router.patch(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel Order",
    description="User can cancel their own order — **only while status is PENDING**.",
)
async def cancel_order(
    order_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = OrderService(db)
    return await service.cancel_by_user(order_id=order_id, user_id=current_user.id)
