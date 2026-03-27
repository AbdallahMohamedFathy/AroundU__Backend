import httpx
import asyncio
from typing import Optional
from src.core.config import settings
from src.core.logger import logger
from src.services.base_ai import BaseAIService

class AISentimentService(BaseAIService):
    def __init__(self):
        timeout = getattr(settings, "AI_TIMEOUT_SECONDS", 10.0)
        super().__init__(
            service_name="AI Sentiment Service", 
            timeout=timeout,
            base_url=getattr(settings, "AI_SENTIMENT_BASE_URL", "") # Assume base url or full url handled
        )
        self.full_url = settings.AI_SENTIMENT_URL

    async def analyze_sentiment(self, comment: str) -> Optional[str]:
        """
        Analyze the sentiment of a review comment using AI.
        """
        if not comment or not comment.strip():
            return None

        # Use the shared retry logic from BaseAIService
        # If base_url is not set, _request_with_retry treats the path as a full URL
        data = await self._request_with_retry(
            "POST", 
            self.full_url, 
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
