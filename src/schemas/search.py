from pydantic import BaseModel, Field
from typing import Optional, List
from src.schemas.place_image import PlaceImageResponse


class SearchParams(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None


class PlaceSearchResponse(BaseModel):
    id: int
    name: str = Field(..., description="Place name")
    category: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Place description")
    rating: float = Field(..., description="Average rating (0-5)")
    review_count: int = Field(..., description="Total review count")
    favorite_count: int = Field(..., description="Total favorite count")
    score: float = Field(..., description="Calculated relevance score (0-1)")
    distance_meters: Optional[float] = Field(None, description="Distance from user in meters (only when lat/lng provided)")
    images: List[PlaceImageResponse] = Field(default_factory=list, description="List of images associated with the place")


class TrendingSearch(BaseModel):
    query: str
    count: int


class SearchMetadata(BaseModel):
    execution_time: float
    count: int
    fallback: bool


class SearchResponse(BaseModel):
    results: List[PlaceSearchResponse]
    metadata: Optional[SearchMetadata] = None
    context: Optional[List[TrendingSearch]] = None
