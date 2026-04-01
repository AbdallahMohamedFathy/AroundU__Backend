import re
import urllib.parse
import httpx
from src.core.logger import logger

def resolve_short_url(url: str) -> str:
    """
    Follows redirects for short Google Maps URLs to find the final landing URL.
    """
    if "goo.gl" not in url and ".page.link" not in url:
        return url
        
    try:
        # Use a real user-agent to avoid being blocked by Google
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        with httpx.Client(follow_redirects=True, headers=headers, timeout=10.0) as client:
            response = client.get(url)
            logger.info(f"Resolved short URL {url} to {response.url}")
            return str(response.url)
    except Exception as e:
        logger.error(f"Error resolving short URL {url}: {e}")
        return url

def extract_coordinates(url: str):
    """
    Extracts latitude and longitude from a Google Maps URL using regex patterns.
    Resolves short URLs (like goo.gl) by following redirects.
    """
    if not url:
        return None

    # 1. Resolve short URL if necessary
    resolved_url = resolve_short_url(url)
    
    # 2. Decode the final URL
    decoded_url = urllib.parse.unquote(resolved_url)
    
    # Prioritized patterns
    patterns = [
        # Pattern 1: Marker coordinates (!3dLAT!4dLON) - Highest precision
        r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)',
        
        # Pattern 2: Viewport / Marker context (@LAT,LON)
        r'@(-?\d+\.\d+),(-?\d+\.\d+)',
        
        # Pattern 3: Query parameter (q=LAT,LON)
        r'[?&]q=([-+]?\d*\.\d+|\d+),([-+]?\d*\.\d+|\d+)',
        
        # Pattern 4: Path coordinates (/LAT,LON)
        r'/([-+]?\d+\.\d+),([-+]?\d+\.\d+)'
    ]

    # Search in both resolved and decoded URL
    for search_text in [resolved_url, decoded_url]:
        for pattern in patterns:
            match = re.search(pattern, search_text)
            if match:
                try:
                    lat = float(match.group(1))
                    lon = float(match.group(2))
                    
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        logger.info(f"Extracted coordinates: {lat}, {lon}")
                        return lat, lon
                except (ValueError, IndexError):
                    continue

    logger.warning(f"Failed to extract coordinates from Google Maps URL: {url} (Resolved: {resolved_url})")
    return None
