import re
import urllib.parse
from src.core.logger import logger

def extract_coordinates(url: str):
    """
    Extracts latitude and longitude from a Google Maps URL using regex patterns.
    Does NOT make any HTTP requests.
    Supports various formats and handles URL encoding.
    """
    if not url:
        return None

    # First, decode the URL in case it's a redirect link (like consent.google.com)
    # The real URL might be inside a query parameter like 'continue' or 'url'
    decoded_url = urllib.parse.unquote(url)
    
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

    # Search in both original and decoded URL
    for search_text in [url, decoded_url]:
        for pattern in patterns:
            match = re.search(pattern, search_text)
            if match:
                try:
                    lat = float(match.group(1))
                    lon = float(match.group(2))
                    
                    # Basic validity check (lat: -90 to 90, lon: -180 to 180)
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        logger.info(f"Extracted coordinates: {lat}, {lon}")
                        return lat, lon
                except (ValueError, IndexError):
                    continue

    logger.warning(f"Failed to extract coordinates from Google Maps URL: {url}")
    return None
