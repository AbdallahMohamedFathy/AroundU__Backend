from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class SubItemCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    is_available: bool = True


class SubItemUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    is_available: Optional[bool] = None


class SubItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    is_available: bool
    item_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
