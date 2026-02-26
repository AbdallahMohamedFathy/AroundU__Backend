from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class FavoriteBase(BaseModel):
    place_id: int


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteResponse(FavoriteBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FavoriteWithPlace(BaseModel):
    id: int
    place_id: int
    created_at: datetime
    place: Optional[dict] = None  # Will contain place details

    model_config = ConfigDict(from_attributes=True)
