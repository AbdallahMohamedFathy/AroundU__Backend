from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ai_service.services.chatbot_service import chatbot_service

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: int
    message: str

class ChatResponse(BaseModel):
    response: str
    recommended_places: Optional[List] = None

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response_data = await chatbot_service.get_response(request.user_id, request.message)
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
