import httpx
import asyncio
from typing import List, Dict, Any, Optional
from src.core.logger import logger
from src.services.base_ai import BaseAIService

class AILocationService(BaseAIService):
    def __init__(self):
        super().__init__(service_name="AI Location Service")
        self.base_url = "https://mazenmaher26-aroundu-location-clustering.hf.space"

    async def predict_cluster(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Predict cluster for a given coordinate."""
        url = f"{self.base_url}/predict"
        return await self._request_with_retry("POST", url, json={"lat": lat, "lon": lon})

    async def get_heatmap(self, points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate heatmap from points."""
        # 1. Filter invalid data (None values)
        valid_points = [
            {
                "lat": p.get("lat"), 
                "lon": p.get("lon"), 
                "cluster": p.get("cluster")
            } 
            for p in points 
            if p.get("lat") is not None and p.get("lon") is not None
        ]
        
        # 2. If empty -> return []
        if not valid_points:
            return []

        # 3. Use new payload structure: {"visits": [...]}
        url = f"{self.base_url}/heatmap"
        data = await self._request_with_retry("POST", url, json={"visits": valid_points})
        
        # 4. Unwrap nested 'hotspots' from AI response to match dashboard expectation
        if data and isinstance(data, dict):
            return data.get("hotspots", [])
        return []

    async def get_opportunities(self, points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get opportunity clusters from points."""
        # Same filtering and structure as heatmap
        valid_points = [
            {
                "lat": p.get("lat"), 
                "lon": p.get("lon"), 
                "cluster": p.get("cluster")
            } 
            for p in points 
            if p.get("lat") is not None and p.get("lon") is not None
        ]
        
        if not valid_points:
            return []

        url = f"{self.base_url}/opportunities"
        
        # AI Service for /opportunities expects 'places' key and specific fields (category, district)
        # We send both 'visits' (per user instruction) and 'places' (per AI service requirement)
        payload = {
            "visits": valid_points,
            "places": valid_points
        }
        
        data = await self._request_with_retry("POST", url, json=payload)
        
        # Unwrap nested 'opportunities' from AI response
        if data and isinstance(data, dict):
            return data.get("opportunities", [])
        return []

    async def get_clusters(self) -> List[Dict[str, Any]]:
        """Get all clusters from the AI service."""
        url = f"{self.base_url}/clusters"
        data = await self._request_with_retry("GET", url)
        return data if data else []

ai_location_service = AILocationService()
