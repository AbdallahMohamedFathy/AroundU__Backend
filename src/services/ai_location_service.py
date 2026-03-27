import httpx
import asyncio
from typing import List, Dict, Any, Optional
from src.core.logger import logger
from src.services.base_ai import BaseAIService

class AILocationService(BaseAIService):
    def __init__(self):
        super().__init__(
            service_name="AI Location Service", 
            base_url="https://mazenmaher26-aroundu-location-clustering.hf.space"
        )

    async def predict_cluster(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Predict cluster for a given coordinate."""
        return await self._request_with_retry("POST", "/predict", json={"lat": lat, "lon": lon})

    async def get_heatmap(self, points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate heatmap from points."""
        # 1. Filter invalid data (lat/lon/cluster is None)
        valid_points = [
            {
                "lat": p.get("lat"), 
                "lon": p.get("lon"), 
                "cluster": p.get("cluster")
            } 
            for p in points 
            if p.get("lat") is not None and p.get("lon") is not None and p.get("cluster") is not None
        ]
        
        # 2. If no valid data -> return empty list and DO NOT call AI
        if not valid_points:
            return []

        # 3. Use required payload structure: {"visits": [...]}
        data = await self._request_with_retry("POST", "/heatmap", json={"visits": valid_points})
        
        # 4. Unwrap nested 'hotspots' from AI response to match dashboard expectation
        if data and isinstance(data, dict):
            return data.get("hotspots", [])
        return []

    async def get_opportunities(self, points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get opportunity clusters from points."""
        # 1. Filter invalid data (lat/lon/cluster is None)
        valid_points = [
            {
                "lat": p.get("lat"), 
                "lon": p.get("lon"), 
                "cluster": p.get("cluster")
            } 
            for p in points 
            if p.get("lat") is not None and p.get("lon") is not None and p.get("cluster") is not None
        ]
        
        # 2. If no valid data -> return empty list and DO NOT call AI
        if not valid_points:
            return []

        # 3. Use required payload structure: {"visits": [...]}
        data = await self._request_with_retry("POST", "/opportunities", json={"visits": valid_points})
        
        # 4. Unwrap nested 'opportunities' from AI response
        if data and isinstance(data, dict):
            return data.get("opportunities", [])
        return []

    async def get_clusters(self) -> List[Dict[str, Any]]:
        """Get all clusters from the AI service."""
        data = await self._request_with_retry("GET", "/clusters")
        return data if data else []

ai_location_service = AILocationService()
