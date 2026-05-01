from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AIInteractionResponse(BaseModel):
    user_id: str
    event_type: str
    place_id: Optional[str] = None
    rating_value: Optional[float] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class AIPlaceResponse(BaseModel):
    place_id: str
    name: str
    category: str
    rating: float
    review_count: int
    lat: Optional[float] = None
    lng: Optional[float] = None

    class Config:
        from_attributes = True

class AIAnalyticsResponse(BaseModel):
    top_rated_places: List[AIPlaceResponse]
    most_visited_places: List[AIPlaceResponse]
    trending_categories: List[str]

class AITrainingDataRow(BaseModel):
    user_id: str
    event_type: str
    place_category: str
    rating_value: Optional[float] = None
    timestamp: datetime
