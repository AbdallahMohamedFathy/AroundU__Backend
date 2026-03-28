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
        """Generate heatmap from points (requires lat, lon, cluster only)."""
        # 1. Map to required schema: lat, lon, cluster
        valid_points = [
            {
                "lat": p.get("lat"), 
                "lon": p.get("lon"), 
                "cluster": p.get("cluster")
            } 
            for p in points 
            if p.get("lat") is not None 
            and p.get("lon") is not None 
            and p.get("cluster") is not None
        ]
        
        # 2. Safety: If no valid data -> return empty list
        if not valid_points:
            return []

        # 3. Log and request
        payload = {"visits": valid_points}
        logger.info(f"Heatmap payload: {payload}")
        data = await self._request_with_retry("POST", "/heatmap", json=payload)
        
        # 4. Unwrap nested 'hotspots' from AI response
        if data and isinstance(data, dict):
            return data.get("hotspots", [])
        return []

    async def get_opportunities(self, points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get opportunity clusters from points (requires full metadata)."""
        # 1. Map to required schema: lat, lon, cluster, category, district
        valid_points = []
        for p in points:
            lat = p.get("lat")
            lon = p.get("lon")
            cluster = p.get("cluster")
            category = p.get("category")
            district = p.get("district")
            
            # Skip if any required metadata is missing
            if all(v is not None for v in [lat, lon, cluster, category, district]):
                valid_points.append({
                    "lat": lat,
                    "lon": lon,
                    "cluster": cluster,
                    "category": category,
                    "district": district
                })
        
        # 2. Safety: If no valid data -> return empty list
        if not valid_points:
            return []

        # 3. Log and request
        payload = {"visits": valid_points}
        logger.info(f"Opportunities payload: {payload}")
        data = await self._request_with_retry("POST", "/opportunities", json=payload)
        
        # 4. Unwrap nested 'opportunities' from AI response
        if data and isinstance(data, dict):
            return data.get("opportunities", [])
        return []

    async def get_clusters(self) -> List[Dict[str, Any]]:
        """Get all clusters from the AI service."""
        data = await self._request_with_retry("GET", "/clusters")
        return data if data else []

ai_location_service = AILocationService()
