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
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    whatsapp_number: Optional[str] = None
    tiktok_url: Optional[str] = None


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
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    whatsapp_number: Optional[str] = None
    tiktok_url: Optional[str] = None
    is_active: Optional[bool] = None




class PlaceResponse(PlaceBase):
    id: int
    rating: float
    review_count: int
    is_active: bool
    created_at: datetime
    distance_km: Optional[float] = None  # Calculated field
    images: List[PlaceImageResponse] = []
    is_favorited: Optional[bool] = False  # Calculated field based on current user

    model_config = ConfigDict(from_attributes=True)


class NearbyPlaceResponse(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=200)
    category: str
    description: Optional[str] = None
    distance: float
    is_favorited: Optional[bool] = False

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

