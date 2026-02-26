import httpx
from typing import List, Dict, Optional
from ai_service.core.config import settings

class ChatbotService:
    def __init__(self):
        self.backend_url = settings.BACKEND_URL

    async def understand_intent(self, message: str) -> str:
        """Basic intent recognition based on keywords."""
        msg = message.lower()
        if any(word in msg for word in ["find", "search", "look for", "show me", "اين", "أبحث"]):
            return "search_places"
        if any(word in msg for word in ["recommend", "suggest", "like", "اقتراح", "ترشيح"]):
            return "recommend_places"
        return "general_chat"

    async def get_response(self, user_id: int, message: str) -> Dict:
        """Main chat logic."""
        intent = await self.understand_intent(message)
        response_text = ""
        recommended_places = []

        if intent == "search_places":
            # Very basic extraction: try to find category or keyword
            # In a real app, we'd use NLP here
            async with httpx.AsyncClient() as client:
                # Search across all places for keywords in the message
                resp = await client.get(f"{self.backend_url}/places/search?q={message}")
                if resp.status_code == 200:
                    recommended_places = resp.json()
                    if recommended_places:
                        response_text = f"Found {len(recommended_places)} places you might like!"
                    else:
                        response_text = "I couldn't find any specific places matching that. Try searching for something else like 'Pizza' or 'Museum'."
                else:
                    response_text = "I'm having trouble searching right now. Can I help with something else?"

        elif intent == "recommend_places":
            from ai_service.services.recommendation_service import recommendation_service
            recommended_places = await recommendation_service.get_recommendations(user_id)
            if recommended_places:
                response_text = "Based on your activity, here are some places I think you'll love!"
            else:
                response_text = "I don't have enough data to recommend places yet. Try favoriting some places first!"

        else:
            response_text = "I am AroundU AI Assistant. I can help you find interesting places, recommend coffee shops, or just chat! How can I help?"

        return {
            "response": response_text,
            "recommended_places": recommended_places
        }

chatbot_service = ChatbotService()
