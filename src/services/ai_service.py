import httpx
import asyncio
from typing import List, Dict, Any, Optional
from src.core.config import settings
from src.core.logger import logger

class AIServiceConnector:
    def __init__(self):
        self.ai_service_url = getattr(settings, "AI_SERVICE_URL", "http://ai_service:8001")
        self.ai_clustering_url = "https://mazenmaher26-aroundu-location-clustering.hf.space"
        self.timeout = 10.0 # Increased for AI processing
        self.max_retries = 3

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Internal helper for resilient requests."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    logger.warning(f"AI Service ({url}) attempt {attempt+1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        logger.error(f"AI Service exhausted all {self.max_retries} retries for {url}.")
                        return None
                    await asyncio.sleep(0.5 * (attempt + 1)) # Simple backoff
        return None

    # --- CHAT & RECOMMENDATIONS (Legacy/Existing) ---
    def _get_api_url(self, path: str) -> str:
        return f"{self.ai_service_url}{path}"

    async def send_chat_message(self, user_id: int, message: str) -> Dict[str, Any]:
        """Forward chat message to AI microservice with resilience."""
        data = await self._request_with_retry(
            "POST", self._get_api_url("/chat/"), 
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
        data = await self._request_with_retry("GET", self._get_api_url(f"/recommendations/{user_id}"))
        if data and isinstance(data, dict):
            return data.get("recommendations", [])
        return []

    # --- NEW CLUSTERING & ANALYTICS ---
    async def predict_cluster(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Predict cluster for a given coordinate."""
        url = f"{self.ai_clustering_url}/predict"
        return await self._request_with_retry("POST", url, json={"lat": lat, "lon": lon})

    async def get_heatmap(self, points: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Generate heatmap from points."""
        url = f"{self.ai_clustering_url}/heatmap"
        data = await self._request_with_retry("POST", url, json=points)
        return data if data else []

    async def get_opportunities(self, points: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Get opportunity clusters from points."""
        url = f"{self.ai_clustering_url}/opportunities"
        data = await self._request_with_retry("POST", url, json=points)
        return data if data else []

ai_connector = AIServiceConnector()
