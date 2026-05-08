from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.dependencies import get_db
from app.orders.services.order_service import OrderService
from app.orders.schemas.order import OrderResponse
from app.auth import get_current_user

router = APIRouter(tags=["Dashboard - Admin"])

@router.get(
    "/all-orders",
    response_model=List[OrderResponse],
    description="Admin can see ALL orders in the system - **Admin only**",
)
async def get_all_orders(db=Depends(get_db), current_user=Depends(get_current_user)):
    # Role check
    if getattr(current_user, "role", "").upper() != "ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    service = OrderService(db)
    orders = await service.order_repo.get_all_orders()
    
    result = []
    for o in orders:
        items_res = [
            OrderItemResponse(
                id=i.id,
                item_id=i.item_id,
                item_name=i.item_name,
                unit_price=i.unit_price,
                quantity=i.quantity,
                total_price=i.total_price,
            ) for i in o.items
        ]
        result.append(OrderResponse(
            id=o.id,
            user_id=o.user_id,
            owner_id=o.owner_id,
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
