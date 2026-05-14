from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

class ItemBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    image_url: Optional[str] = None
    is_available: bool = True
    sub_category_id: Optional[int] = None
    place_id: Optional[int] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    sub_category_id: Optional[int] = None

class ItemResponse(ItemBase):
    id: int
    subcategory_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class ItemPaginationResponse(BaseModel):
    items: list[ItemResponse]
    total: int
    page: int
    size: int
    pages: int
