import httpx
import asyncio
from typing import Optional
from src.core.config import settings
from src.core.logger import logger
from src.services.base_ai import BaseAIService

class AISentimentService(BaseAIService):
    def __init__(self):
        super().__init__(
            service_name="AI Sentiment Service", 
            base_url="https://mazenmaher26-aroundu-sentiment.hf.space",
            timeout=10.0,
            max_retries=3
        )

    async def get_health(self):
        return await self._request_with_retry("GET", "/health")

    async def analyze_sentiment(self, comment: str) -> Optional[str]:
        """
        Analyze the sentiment of a review comment using AI.
        """
        if not comment or not comment.strip():
            return None

        # Hit the new /predict endpoint
        data = await self._request_with_retry(
            "POST", 
            "/predict", 
            json={"text": comment}
        )

        if not data:
            return None

        sentiment = data.get("sentiment") or data.get("label")
        if sentiment:
            sentiment = sentiment.lower()
            
        if sentiment in ("positive", "negative"):
            return sentiment
        
        logger.warning(f"Unexpected sentiment value received: {sentiment}")
        return None

# For backward compatibility
_service = AISentimentService()

async def analyze_sentiment(comment: str) -> Optional[str]:
    return await _service.analyze_sentiment(comment)
