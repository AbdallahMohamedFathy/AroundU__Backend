from pydantic import BaseModel, ConfigDict, HttpUrl
from datetime import datetime
from typing import Optional


class PlaceImageBase(BaseModel):
    image_url: str
    is_primary: bool = False


class PlaceImageCreate(PlaceImageBase):
    place_id: int


class PlaceImageResponse(PlaceImageBase):
    id: int
    place_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
