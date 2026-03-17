import httpx
import asyncio
from typing import List, Dict, Any, Optional
from src.core.logger import logger

class AIAnomalyService:
    def __init__(self):
        self.base_url = "https://mazenmaher26-aroundu-anomaly-detection.hf.space"
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
                    logger.warning(f"AI Anomaly Service ({url}) attempt {attempt+1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        logger.error(f"AI Anomaly Service exhausted all {self.max_retries} retries for {url}.")
                        return None
                    await asyncio.sleep(0.5 * (attempt + 1))
        return None

    async def detect_anomalies(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in arbitrary interaction metric data."""
        # e.g. [{"metric_name": "visits", "value": 150}] -> returns anomalies
        res = await self._request_with_retry("POST", "/detect", json=data)
        return res if res else []

    async def get_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary stats for the provided data."""
        res = await self._request_with_retry("POST", "/summary", json=data)
        return res if res else {}

    async def get_place_anomalies(self, place_id: int) -> List[Dict[str, Any]]:
        """Get specifically place anomalies by ID."""
        # Note: the user requested POST /place-anomalies
        res = await self._request_with_retry("POST", "/place-anomalies", json={"place_id": place_id})
        return res if res else []

ai_anomaly_service = AIAnomalyService()
