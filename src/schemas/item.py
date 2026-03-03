from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class ItemBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    discount: Decimal = Field(default=Decimal('0'), ge=0, le=100)
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)

class ItemResponse(ItemBase):
    id: int
    place_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
