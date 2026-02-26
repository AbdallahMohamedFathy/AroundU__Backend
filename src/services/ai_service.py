import httpx
import asyncio
from typing import List, Dict, Any, Optional
from src.core.config import settings
from src.core.logger import logger

class AIServiceConnector:
    def __init__(self):
        self.ai_service_url = getattr(settings, "AI_SERVICE_URL", "http://ai_service:8001")
        self.timeout = 3.0
        self.max_retries = 3

    async def _request_with_retry(self, method: str, path: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Internal helper for resilient requests."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    url = f"{self.ai_service_url}{path}"
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    logger.warning(f"AI Service attempt {attempt+1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        logger.error(f"AI Service exhausted all {self.max_retries} retries.")
                        return None
                    await asyncio.sleep(0.5 * (attempt + 1)) # Simple backoff
        return None

    async def send_chat_message(self, user_id: int, message: str) -> Dict[str, Any]:
        """Forward chat message to AI microservice with resilience."""
        data = await self._request_with_retry(
            "POST", "/chat/", 
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
        data = await self._request_with_retry("GET", f"/recommendations/{user_id}")
        if data and isinstance(data, dict):
            return data.get("recommendations", [])
        return []

ai_connector = AIServiceConnector()
