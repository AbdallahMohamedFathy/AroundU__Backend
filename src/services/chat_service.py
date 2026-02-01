from sqlalchemy.orm import Session
from src.schemas.chat import ChatResponse, PlaceSuggestion
from src.services.search_service import search_places
from src.models.chat_message import ChatMessage
import random

def process_chat_message(db: Session, user_id: int, message: str) -> ChatResponse:
    # "AI" Logic: Rule-based intent recognition + Search
    
    msg_lower = message.lower()
    reply = ""
    suggestions = []
    
    # 1. Intent: Recommendation
    if any(word in msg_lower for word in ["recommend", "place", "restaurant", "cafe", "food", "eat", "looking for", "nearby"]):
        # Extract keywords (very naive)
        keywords = msg_lower.replace("i'm", "").replace("looking for", "").replace("recommend", "").strip()
        
        # Search DB
        places = search_places(db, query=keywords)
        if places:
            places = places[:3]  # Limit to top 3
        
        if places:
            reply = f"I found {len(places)} places that match your request."
            suggestions = [
                PlaceSuggestion(
                    name=p.name,
                    rating=p.rating,
                    distance=f"{random.randint(1, 50) / 10} km" # Mock distance for now as we don't have geospatial calc yet
                ) for p in places
            ]
        else:
            reply = "I couldn't find any specific places matching that, but here are some popular spots."
            # Fallback to top rated
            places = search_places(db)
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

    # Save to DB
    history = ChatMessage(user_id=user_id, message=message, reply=reply)
    db.add(history)
    db.commit()
    
    return ChatResponse(reply=reply, suggestions=suggestions)
