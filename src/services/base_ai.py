import httpx
import asyncio
from typing import Dict, Any, Optional
from src.core.logger import logger

class BaseAIService:
    def __init__(self, service_name: str, timeout: float = 10.0, max_retries: int = 3):
        self.service_name = service_name
        self.timeout = timeout
        self.max_retries = max_retries

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Internal helper for resilient requests with retries and error handling.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    logger.warning(f"{self.service_name} ({url}) attempt {attempt+1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        logger.error(f"{self.service_name} exhausted all {self.max_retries} retries for {url}.")
                        return None
                    await asyncio.sleep(0.5 * (attempt + 1)) # Exponential backoff
        return None
