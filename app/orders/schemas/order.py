from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, validator
from app.orders.enums.enums import OrderType, OrderStatus


class OrderItemCreate(BaseModel):
    item_id: int = Field(..., gt=0)
    sub_item_id: Optional[int] = Field(None, gt=0)
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    place_id: int = Field(..., gt=0, description="The Place (branch) to order from")
    order_type: OrderType
    full_name: str = Field(..., min_length=1)
    phone_number: str = Field(..., min_length=1)
    address: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemCreate]

    @validator('address')
    def address_required_for_cod(cls, v, values):
        if values.get('order_type') == OrderType.CASH_ON_DELIVERY and not v:
            raise ValueError('address is required for CASH_ON_DELIVERY orders')
        return v


class OrderItemResponse(BaseModel):
    id: int
    item_id: int
    sub_item_id: Optional[int] = None
    item_name: str
    image_url: Optional[str] = None
    unit_price: float
    quantity: int
    total_price: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    user_id: int
    place_id: Optional[int]
    order_type: OrderType
    status: OrderStatus
    full_name: str
    phone_number: str
    address: Optional[str]
    notes: Optional[str]
    delivery_fee: float = 0.0
    total_price: float
    items: List[OrderItemResponse] = []
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
