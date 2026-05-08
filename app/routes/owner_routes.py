from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.dependencies import get_db
from app.orders.services.order_service import OrderService
from app.orders.schemas.order import OrderResponse
from app.auth import get_current_user

router = APIRouter(tags=["Owner"])

@router.get(
    "/orders",
    response_model=List[OrderResponse],
    description="Owner receives list of orders placed to their business – **for owner**",
)
async def get_owner_orders(db=Depends(get_db), current_user=Depends(get_current_user)):
    # Simple role check (mocked)
    if getattr(current_user, "role", None) != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    service = OrderService(db)
    orders = await service.order_repo.get_owner_orders(current_user.id)
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
