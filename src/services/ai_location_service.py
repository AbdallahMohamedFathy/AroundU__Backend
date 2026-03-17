import httpx
import asyncio
from typing import List, Dict, Any, Optional
from src.core.logger import logger

class AILocationService:
    def __init__(self):
        self.base_url = "https://mazenmaher26-aroundu-location-clustering.hf.space"
        self.timeout = 10.0
        self.max_retries = 3

    async def _request_with_retry(self, method: str, path: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Internal helper for resilient requests."""
        url = f"{self.base_url.rstrip('/')}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    logger.warning(f"AI Location Service ({url}) attempt {attempt+1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        logger.error(f"AI Location Service exhausted all {self.max_retries} retries for {url}.")
                        return None
                    await asyncio.sleep(0.5 * (attempt + 1))
        return None

    async def predict_cluster(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Predict cluster for a given coordinate."""
        return await self._request_with_retry("POST", "/predict", json={"lat": lat, "lon": lon})

    async def get_heatmap(self, points: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Generate heatmap from points."""
        data = await self._request_with_retry("POST", "/heatmap", json=points)
        return data if data else []

    async def get_opportunities(self, points: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Get opportunity clusters from points."""
        data = await self._request_with_retry("POST", "/opportunities", json=points)
        return data if data else []

    async def get_clusters(self) -> List[Dict[str, Any]]:
        """Get all clusters from the AI service."""
        data = await self._request_with_retry("GET", "/clusters")
        return data if data else []

ai_location_service = AILocationService()
