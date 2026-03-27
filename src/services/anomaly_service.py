import httpx
import asyncio
from typing import List, Dict, Any, Optional
from src.core.logger import logger
from src.services.base_ai import BaseAIService

class AIAnomalyService(BaseAIService):
    def __init__(self):
        super().__init__(service_name="AI Anomaly Service")
        self.base_url = "https://mazenmaher26-aroundu-anomaly-detection.hf.space"

    async def detect_anomalies(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in arbitrary interaction metric data."""
        url = f"{self.base_url}/detect"
        res = await self._request_with_retry("POST", url, json=data)
        return res if res else []

    async def get_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary stats for the provided data."""
        url = f"{self.base_url}/summary"
        res = await self._request_with_retry("POST", url, json=data)
        return res if res else {}

    async def get_place_anomalies(self, place_id: int) -> List[Dict[str, Any]]:
        """Get specifically place anomalies by ID."""
        url = f"{self.base_url}/place-anomalies"
        res = await self._request_with_retry("POST", url, json={"place_id": place_id})
        return res if res else []

ai_anomaly_service = AIAnomalyService()
