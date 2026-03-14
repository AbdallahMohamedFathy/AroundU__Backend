from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime


class PlaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    category_id: int


class PlaceCreate(PlaceBase):
    pass

class PlaceCreateRequest(BaseModel):
    place_data: PlaceCreate
    owner_user_id: int

class PlaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    location_link: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class PlaceImageInfo(BaseModel):
    id: int
    image_url: str
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)


class PlaceResponse(PlaceBase):
    id: int
    rating: float
    review_count: int
    is_active: bool
    created_at: datetime
    distance_km: Optional[float] = None  # Calculated field
    images: List[PlaceImageInfo] = []
    is_favorited: Optional[bool] = False  # Calculated field based on current user

    model_config = ConfigDict(from_attributes=True)


class NearbyPlaceResponse(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=200)
    category: str
    description: Optional[str] = None
    distance: float

    model_config = ConfigDict(from_attributes=True)


class NearbyPlaceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[NearbyPlaceResponse]


class PlaceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[PlaceResponse]

