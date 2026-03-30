from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from src.schemas.place_image import PlaceImageResponse


class RecommendedPlaceResponse(BaseModel):
    """Single recommended place with scoring breakdown."""
    id: int
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    category: str
    latitude: float
    longitude: float
    distance_km: float = Field(..., description="Distance from user in kilometers")
    avg_rating: float = Field(..., description="Average rating (0-5)")
    review_count: int = Field(0, description="Number of reviews")
    favorite_count: int = Field(0, description="Total times favorited")
    score: float = Field(..., description="Composite recommendation score (0-1)")
    images: List[PlaceImageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class RecommendationListResponse(BaseModel):
    """Paginated recommendation response."""
    total_candidates: int = Field(..., description="Total places evaluated")
    returned: int = Field(..., description="Number of places returned")
    radius_km: float = Field(..., description="Search radius used")
    items: List[RecommendedPlaceResponse]
