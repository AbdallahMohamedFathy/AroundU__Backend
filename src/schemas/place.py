from pydantic import BaseModel
from typing import Optional

class PlaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    rating: float
    latitude: float
    longitude: float
    category_id: int

class PlaceResponse(PlaceBase):
    id: int
    distance_km: Optional[float] = None # Calculated field

    class Config:
        orm_mode = True

