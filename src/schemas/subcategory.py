from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class SubCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    image_url: Optional[str] = None
    category_id: int

class SubCategoryCreate(SubCategoryBase):
    pass

class SubCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    image_url: Optional[str] = None
    category_id: Optional[int] = None

class SubCategoryResponse(SubCategoryBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
