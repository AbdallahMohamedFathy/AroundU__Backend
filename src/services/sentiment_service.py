import requests
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)

def analyze_sentiment(comment: str) -> str | None:
    """
    Calls the AI service to analyze the sentiment of a review comment.
    Returns 'positive', 'negative', or None if analysis fails or comment is empty.
    """
    if not comment or not comment.strip():
        return None

    try:
        response = requests.post(
settings.AI_SENTIMENT_URL,
            json={"text": comment},
            timeout=settings.AI_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        
        data = response.json()
        sentiment = data.get("sentiment")
        
        if sentiment in ("positive", "negative"):
            return sentiment
        
        logger.warning(f"Unexpected sentiment value received: {sentiment}")
        return None
        
    except requests.RequestException as e:
        logger.error(f"Failed to connect to AI sentiment service: {e}")
        return None
    except Exception as e:
        logger.error(f"Error during sentiment analysis: {e}")
        return None
