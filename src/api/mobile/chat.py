from typing import List, Dict, Any
from src.models.user import User
from src.services.ai_service import ai_connector
from src.core.dependencies import get_uow, get_conversation_repository, limiter, get_current_user
from fastapi import APIRouter, Depends, HTTPException, status, Request

router = APIRouter()

@router.post("/")
@limiter.limit("20/minute")
async def chat_with_ai(
    request: Request,
    payload: Dict[str, str],
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user)
):
    message_content = payload.get("message")
    if not message_content:
        raise HTTPException(status_code=400, detail="Message is required")

    with uow:
        # 1. Get or create a conversation for the user
        conversation = uow.conversation_repository.get_latest_for_user(current_user.id)
        if not conversation:
            from src.models.conversation import Conversation # Lazy import
            conversation = Conversation(user_id=current_user.id)
            uow.conversation_repository.add(conversation)
            uow.session.flush() # Get ID

        # 2. Save user message
        from src.models.message import Message # Lazy import
        user_msg = Message(
            conversation_id=conversation.id,
            sender="user",
            content=message_content
        )
        uow.message_repository.add(user_msg)
        
        # 3. Get AI response from microservice
        ai_response_data = await ai_connector.send_chat_message(current_user.id, message_content)
        
        # 4. Save AI message
        ai_msg = Message(
            conversation_id=conversation.id,
            sender="ai",
            content=ai_response_data.get("response", "")
        )
        uow.message_repository.add(ai_msg)
        uow.commit()

    return ai_response_data

@router.get("/recommendations")
async def get_user_recommendations(
    current_user: User = Depends(get_current_user)
):
    recommendations = await ai_connector.get_recommendations(current_user.id)
    return {"recommendations": recommendations}
