from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InteractionBase(BaseModel):
    place_id: int
    type: str # visit, call, direction, order, save
    user_lat: Optional[float] = None
    user_lon: Optional[float] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionResponse(InteractionBase):
    id: int
    user_id: Optional[int]
    cluster_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
