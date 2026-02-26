"""
Service layer for managing chat (Refactored for Phase D)
"""
import random
from typing import List, Optional
from src.core.unit_of_work import UnitOfWork
from src.schemas.chat import ChatResponse, PlaceSuggestion
from src.services import search_service
from src.core.exceptions import APIException
from fastapi import status

def process_chat_message(uow: UnitOfWork, user_id: int, message: str) -> ChatResponse:
    # "AI" Logic: Rule-based intent recognition + Search
    
    msg_lower = message.lower()
    reply = ""
    suggestions = []
    
    # 1. Intent: Recommendation
    if any(word in msg_lower for word in ["recommend", "place", "restaurant", "cafe", "food", "eat", "looking for", "nearby"]):
        # Extract keywords
        keywords = msg_lower.replace("i'm", "").replace("looking for", "").replace("recommend", "").strip()
        
        # Search DB via SearchService (which is now refactored)
        places = search_service.search_places(uow, query=keywords)
        if places:
            places = places[:3]
        
        if places:
            reply = f"I found {len(places)} places that match your request."
            suggestions = [
                PlaceSuggestion(
                    name=p.name,
                    rating=p.rating,
                    distance=f"{random.randint(1, 50) / 10} km"
                ) for p in places
            ]
        else:
            reply = "I couldn't find any specific places matching that, but here are some popular spots."
            places = search_service.search_places(uow)
            if places:
                places = places[:3]
            suggestions = [
                PlaceSuggestion(name=p.name, rating=p.rating, distance="1.2 km") for p in places
            ]
            
    # 2. Intent: Greeting
    elif any(word in msg_lower for word in ["hello", "hi", "hey"]):
        reply = "Hello! I'm your AroundU assistant. How can I help you find a place today?"
        
    # 3. Default
    else:
        reply = "I'm not sure I understand. Try asking for recommendations like 'Italian food' or 'Cafes nearby'."

    # Save to DB via ChatMessageRepository
    with uow:
        from src.models.chat_message import ChatMessage # Lazy import
        history = ChatMessage(user_id=user_id, message=message, reply=reply)
        uow.chat_message_repository.add(history)
        uow.commit()
    
    return ChatResponse(reply=reply, suggestions=suggestions)
