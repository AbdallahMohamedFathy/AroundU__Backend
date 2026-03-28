import httpx
import asyncio
from typing import List, Dict, Any, Optional
from src.core.logger import logger
from src.services.base_ai import BaseAIService

class AIAnomalyService(BaseAIService):
    def __init__(self):
        super().__init__(
            service_name="AI Anomaly Service",
            base_url="https://mazenmaher26-aroundu-anomaly-detection.hf.space"
        )

    async def detect_anomalies(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in aggregated interaction metric data."""
        if not data:
            return []
            
        # 3. Log and request
        payload = {"visits": data}
        logger.info(f"Anomaly payload (/detect): {payload}")
        res = await self._request_with_retry("POST", "/detect", json=payload)
        
        # 4. Unwrap nested 'anomalies' or 'visits' from AI response
        if res and isinstance(res, dict):
            return res.get("anomalies", res.get("visits", []))
        return res if res else []

    async def get_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary stats for the provided real anomaly records."""
        if not data:
            return {}
            
        # Wrap list in dictionary as required by AI schema: {"anomalies": [...]}
        payload = {"anomalies": data}
        logger.info(f"Anomaly payload (/summary): {payload}")
        res = await self._request_with_retry("POST", "/summary", json=payload)
        return res if res else {}

    async def get_place_anomalies(self, place_id: int) -> List[Dict[str, Any]]:
        """Get specifically place anomalies by ID."""
        # AI expects both place_id and anomalies list (based on latest 422 error)
        res = await self._request_with_retry(
            "POST", "/place-anomalies", 
            json={"place_id": place_id, "anomalies": []}
        )
        
        # Unwrap if nested
        if res and isinstance(res, dict):
            return res.get("anomalies", [])
        return res if res else []

ai_anomaly_service = AIAnomalyService()
