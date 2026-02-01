from pydantic import BaseModel, Field
from typing import Optional, List
from .place import PlaceResponse

class SearchParams(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None

class TrendingSearch(BaseModel):
    query: str
    count: int

class SearchResponse(BaseModel):
    results: List[PlaceResponse]
