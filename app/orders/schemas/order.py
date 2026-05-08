from typing import List, Optional

from pydantic import BaseModel, Field, validator
from app.orders.enums.enums import OrderType, OrderStatus

class OrderItemCreate(BaseModel):
    item_id: int = Field(..., gt=0)
    item_name: str = Field(..., min_length=1)
    unit_price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

    @validator('unit_price')
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError('unit_price must be positive')
        return v

class OrderCreate(BaseModel):
    place_id: Optional[int] = Field(None, gt=0)
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

from datetime import datetime

class OrderItemResponse(BaseModel):
    id: int
    item_id: int
    item_name: str
    unit_price: float
    quantity: int
    total_price: float

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    owner_id: int
    place_id: Optional[int]
    order_type: OrderType
    status: OrderStatus
    full_name: str
    phone_number: str
    address: Optional[str]
    notes: Optional[str]
    total_price: float
    items: List[OrderItemResponse] = []
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
