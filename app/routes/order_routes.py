from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.dependencies import get_db
from app.orders.services.order_service import OrderService
from app.orders.schemas.order import OrderCreate, OrderResponse, OrderStatus
from app.auth import get_current_user

# Group all order endpoints under the "Orders" tag in Swagger UI
router = APIRouter(tags=["Orders"])

@router.post(
    "/checkout/{owner_id}",
    response_model=OrderResponse,
    description="Create a new order (checkout) – **for user**",
)
async def checkout_order(
    owner_id: int,
    order_data: OrderCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = OrderService(db)
    return await service.checkout(user_id=current_user.id, owner_id=owner_id, order_data=order_data)

@router.get(
    "/my",
    response_model=List[OrderResponse],
    description="Retrieve authenticated user's orders – **for user**",
)
async def get_my_orders(db=Depends(get_db), current_user=Depends(get_current_user)):
    service = OrderService(db)
    orders = await service.order_repo.get_user_orders(current_user.id)
    result = []
    for o in orders:
        result.append(OrderResponse(
            id=o.id,
            user_id=o.user_id,
            owner_id=o.owner_id,
            order_type=o.order_type,
            status=o.status,
            full_name=o.full_name,
            phone_number=o.phone_number,
            address=o.address,
            notes=o.notes,
            total_price=o.total_price,
            items=[],  # omitted for brevity
            created_at=o.created_at.isoformat() if o.created_at else None,
        ))
    return result

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    description="Get a specific order – **for user**",
)
async def get_order(order_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = OrderService(db)
    order = await service.order_repo.get_order(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    items_res = []
    for i in order.items:
        items_res.append({
            "id": i.id,
            "item_id": i.item_id,
            "item_name": i.item_name,
            "unit_price": i.unit_price,
            "quantity": i.quantity,
            "total_price": i.total_price,
        })
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        owner_id=order.owner_id,
        order_type=order.order_type,
        status=order.status,
        full_name=order.full_name,
        phone_number=order.phone_number,
        address=order.address,
        notes=order.notes,
        total_price=order.total_price,
        items=items_res,
        created_at=order.created_at.isoformat() if order.created_at else None,
    )

@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    description="Update order status – **for owner** (or admin)",
)
async def update_order_status(
    order_id: int,
    new_status: OrderStatus,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = OrderService(db)
    # Real implementation would verify role (owner/admin)
    return await service.change_status(order_id=order_id, new_status=new_status, actor="owner")

@router.patch(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    description="Cancel an order – **for user** (only while PENDING)",
)
async def cancel_order(
    order_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = OrderService(db)
    return await service.cancel_by_user(order_id=order_id, user_id=current_user.id)
