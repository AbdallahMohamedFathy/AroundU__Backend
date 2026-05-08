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
    orders = await service.order_repo.get_user_orders_all() # need to implement this
    # ... placeholder logic ...
    return []
