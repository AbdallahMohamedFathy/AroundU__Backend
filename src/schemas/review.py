from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class ReviewBase(BaseModel):
    rating: float = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewCreate(ReviewBase):
    place_id: int


class ReviewUpdate(BaseModel):
    rating: Optional[float] = Field(None, ge=1, le=5, description="Rating between 1 and 5")
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewResponse(ReviewBase):
    id: int
    user_id: int
    place_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewWithUser(ReviewResponse):
    user_name: str  # We'll populate this from the user relationship

    model_config = ConfigDict(from_attributes=True)
