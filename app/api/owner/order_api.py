from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from pydantic import BaseModel

from src.api.dashboard.dependencies import owner_guard
from app.dependencies import get_db
from app.orders.services.order_service import OrderService
from app.orders.schemas.order import OrderResponse



class TopItemResponse(BaseModel):
    item_id: int
    item_name: str
    image_url: Optional[str] = None
    unit_price: float
    total_ordered: int

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
            delivery_fee=getattr(o, 'delivery_fee', 0.0),
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
            delivery_fee=getattr(o, 'delivery_fee', 0.0),
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
    return await service.change_status(order_id=order_id, new_status=OrderStatus(new_status))


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Order",
    description=(
        "Owner deletes an order from their place. "
        "Only orders with a final status (COMPLETED, CANCELLED, REJECTED) can be deleted."
    ),
)
async def delete_order(
    order_id: int,
    db=Depends(get_db),
    current_user=Depends(owner_guard),
):
    from app.orders.enums.enums import OrderStatus
    from src.models.place import Place
    from sqlalchemy import select as sa_select

    user_role = str(getattr(current_user, "role", "")).upper()
    if user_role != "OWNER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")

    service = OrderService(db)
    order = await service.order_repo.get_order(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Verify the order belongs to one of the owner's places
    if order.place_id:
        place_result = await db.execute(
            sa_select(Place).where(Place.id == order.place_id, Place.owner_id == current_user.id)
        )
        if not place_result.scalars().first():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this order")

    final_statuses = {OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REJECTED}
    if order.status not in final_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only completed, cancelled, or rejected orders can be deleted (current status: {order.status})",
        )

    await service.order_repo.delete_order(order)
    await db.commit()


@router.get(
    "/place/{place_id}/top-items",
    response_model=List[TopItemResponse],
    summary="Top Ordered Items for a Place",
    description=(
        "Returns the most-ordered items for a specific place, "
        "sorted from most to least ordered. "
        "Shows item name, price (snapshot at order time), and total quantity ordered."
    ),
)
async def get_top_ordered_items(
    place_id: int,
    limit: int = Query(10, ge=1, le=100, description="Max items to return"),
    db=Depends(get_db),
    current_user=Depends(owner_guard),
):
    from sqlalchemy import select, func
    from sqlalchemy.sql.expression import coalesce
    from app.orders.models.order_models import Order, OrderItem
    from app.orders.enums.enums import OrderStatus
    from src.models.place import Place
    from src.models.item import Item

    # Verify ownership
    place_result = await db.execute(
        select(Place).where(Place.id == place_id, Place.owner_id == current_user.id)
    )
    if not place_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Place not found or access denied",
        )

    result = await db.execute(
        select(
            OrderItem.item_id,
            coalesce(func.max(Item.name), func.max(OrderItem.item_name)).label("item_name"),
            coalesce(func.max(Item.image_url), func.max(OrderItem.image_url)).label("image_url"),
            coalesce(func.max(Item.price), func.max(OrderItem.unit_price)).label("unit_price"),
            func.sum(OrderItem.quantity).label("total_ordered"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .outerjoin(Item, OrderItem.item_id == Item.id)
        .where(
            Order.place_id == place_id,
            Order.status != OrderStatus.CANCELLED,
        )
        .group_by(OrderItem.item_id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )

    rows = result.all()
    return [
        TopItemResponse(
            item_id=row.item_id,
            item_name=row.item_name,
            image_url=row.image_url,
            unit_price=float(row.unit_price) if row.unit_price else 0.0,
            total_ordered=row.total_ordered,
        )
        for row in rows
    ]
