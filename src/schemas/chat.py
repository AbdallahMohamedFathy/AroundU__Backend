from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str

class PlaceSuggestion(BaseModel):
    name: str
    rating: float
    distance: str

class ChatResponse(BaseModel):
    reply: str
    suggestions: List[PlaceSuggestion] = []
