from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.schemas.chat import ChatRequest, ChatResponse
from src.api.v1.auth import get_current_user
from src.models.user import User
from src.services.chat_service import process_chat_message

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
def chat_message(
    request: ChatRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return process_chat_message(db, current_user.id, request.message)
