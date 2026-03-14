from pydantic import BaseModel, ConfigDict, HttpUrl
from datetime import datetime
from typing import Optional


class PlaceImageBase(BaseModel):
    image_url: str
    image_type: str # 'place' or 'menu'
    caption: Optional[str] = None


class PlaceImageCreate(PlaceImageBase):
    pass


class PlaceImageResponse(PlaceImageBase):
    id: int
    place_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
