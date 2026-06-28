from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from src.schemas.place_image import PlaceImageResponse


class PlaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[List[str]] = Field(default_factory=list)
    website: Optional[str] = Field(None, max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    category_id: int
    parent_id: Optional[int] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    whatsapp_number: Optional[str] = None
    tiktok_url: Optional[str] = None
    delivery_price: float = 0.0
    is_free_delivery: bool = False
    is_accepting_orders: bool = True
    accepts_delivery: bool = True
    accepts_takeaway: bool = True
    working_hours: Optional[str] = None
    is_open: bool = True


class PlaceCreate(PlaceBase):
    pass

class PlaceCreateRequest(BaseModel):
    place_data: PlaceCreate
    owner_user_id: int

class PlaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[List[str]] = None
    website: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    location_link: Optional[str] = None
    category_id: Optional[int] = None
    parent_id: Optional[int] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    whatsapp_number: Optional[str] = None
    tiktok_url: Optional[str] = None
    delivery_price: Optional[float] = None
    is_free_delivery: Optional[bool] = None
    is_accepting_orders: Optional[bool] = None
    accepts_delivery: Optional[bool] = None
    accepts_takeaway: Optional[bool] = None
    working_hours: Optional[str] = None
    is_active: Optional[bool] = None
    is_open: Optional[bool] = None




class PlaceResponse(PlaceBase):
    id: int
    rating: float
    review_count: int
    is_active: bool
    is_open: bool = True
    is_accepting_orders: bool = True
    accepts_delivery: bool = True
    accepts_takeaway: bool = True
    created_at: datetime
    distance_km: Optional[float] = None
    images: List[PlaceImageResponse] = []
    branches: List['PlaceResponse'] = []
    is_favorited: Optional[bool] = False

    model_config = {"from_attributes": True}


class NearbyPlaceResponse(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=200)
    category: str
    description: Optional[str] = None
    distance_km: float
    delivery_price: float = 0.0
    is_free_delivery: bool = False
    working_hours: Optional[str] = None
    is_open: bool = True
    is_favorited: Optional[bool] = False

    model_config = {"from_attributes": True}


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

