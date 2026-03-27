import httpx
import asyncio
from typing import List, Dict, Any, Optional
from src.core.config import settings
from src.core.logger import logger
from src.services.base_ai import BaseAIService

class AIServiceConnector(BaseAIService):
    def __init__(self):
        super().__init__(service_name="AI Service (Main)")
        self.ai_service_url = getattr(settings, "AI_SERVICE_URL", "http://ai_service:8001").rstrip("/")

    # --- CHAT & RECOMMENDATIONS ---
    def _get_api_url(self, path: str) -> str:
        return f"{self.ai_service_url}{path}"

    async def send_chat_message(self, user_id: int, message: str) -> Dict[str, Any]:
        """Forward chat message to AI microservice with resilience."""
        url = self._get_api_url("/chat/")
        data = await self._request_with_retry(
            "POST", url, 
            json={"user_id": user_id, "message": message}
        )
        if data:
            return data
        
        # Fallback response to avoid 500
        return {
            "response": "I'm currently having trouble connecting to my AI core. Please try again in a moment.",
            "recommended_places": []
        }

    async def get_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Fetch recommendations from AI microservice with resilience."""
        url = self._get_api_url(f"/recommendations/{user_id}")
        data = await self._request_with_retry("GET", url)
        if data and isinstance(data, dict):
            return data.get("recommendations", [])
        return []

ai_connector = AIServiceConnector()
