from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class PropertyBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: float = Field(..., ge=0)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[float] = Field(None, ge=0)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    is_available: Optional[bool] = None
    main_image_url: Optional[str] = None
    image_ids_to_delete: Optional[List[int]] = Field(default_factory=list)


class PropertyImageResponse(BaseModel):
    id: int
    image_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PropertyResponse(PropertyBase):
    id: int
    main_image_url: Optional[str] = None
    is_available: bool
    owner_id: int
    created_at: datetime
    updated_at: datetime
    images: List[PropertyImageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PropertyShortResponse(BaseModel):
    id: int
    title: str
    price: float
    main_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PropertyListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[PropertyShortResponse]
