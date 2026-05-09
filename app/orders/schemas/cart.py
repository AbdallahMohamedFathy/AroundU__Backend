from typing import List, Optional

from pydantic import BaseModel, Field, validator

class CartItemCreate(BaseModel):
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

class CartItemResponse(BaseModel):
    id: int
    item_id: int
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    place_id: int
    total_price: float
    items: List[CartItemResponse] = []
    created_at: Optional[str]

    class Config:
        from_attributes = True
