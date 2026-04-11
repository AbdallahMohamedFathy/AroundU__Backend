"""
api/mobile/ai.py
================
Mobile AI chatbot endpoints – authenticated, proxied through backend.

Routes
------
POST /api/mobile/ai/chat    – send a message, get a structured reply
GET  /api/mobile/ai/health  – proxy the AI service health check
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, status
from pydantic import BaseModel, Field

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.core.logger import logger
from src.models.user import User
from src.services import chatbot_service

router = APIRouter()


# ──────────────────────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:    str            = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str]  = Field(None, description="Omit to auto-generate")
    user_lat:   Optional[float] = None
    user_lon:   Optional[float] = None


class ChatResponse(BaseModel):
    reply:       str
    intent:      str
    confidence:  float
    entities:    dict
    best_place:  Optional[dict] = None
    session_id:  str
    is_fallback: bool = False


class HealthResponse(BaseModel):
    status:        str
    models_loaded: bool


# ──────────────────────────────────────────────────────────────────────────────
# GET /health  – proxy AI health
# ──────────────────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="AI Chatbot Service Health",
    tags=["Mobile - AI"],
)
async def ai_health():
    """
    Proxies the health check to the external AI chatbot.
    Public endpoint – no auth required (safe: no data exposed).
    """
    result = await chatbot_service.check_health()
    return result


# ──────────────────────────────────────────────────────────────────────────────
# POST /chat  – main chatbot endpoint
# ──────────────────────────────────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with AI assistant",
    tags=["Mobile - AI"],
)
async def chat_with_ai(
    body:             ChatRequest,
    background_tasks: BackgroundTasks,
    current_user:     User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Authenticated chatbot endpoint.

    - Injects user context (interactions, favorites, location) into every request.
    - Logs every exchange to `ai_interactions` table.
    - Fires a push notification if AI recommends a place.
    - Returns a structured response; falls back gracefully if AI is down.
    """
    logger.info(
        f"[AI chat] user_id={current_user.id} | "
        f"intent_preview={body.message[:60]!r}"
    )

    result = await chatbot_service.chat(
        db=db,
        user_id=current_user.id,
        user_role=current_user.role,
        message=body.message,
        session_id=body.session_id,
        user_lat=body.user_lat,
        user_lon=body.user_lon,
        background_tasks=background_tasks,
    )

    return result
