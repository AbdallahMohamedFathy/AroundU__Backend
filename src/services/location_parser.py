import requests
import re
from fastapi import HTTPException, status
from src.core.logger import logger

def extract_coordinates_from_google_maps(url: str):
    """
    Extracts latitude and longitude from various Google Maps URL formats.
    Prioritizes marker coordinates over viewport coordinates.
    """
    if not url:
        return None, None

    # 1. Expand short links
    if "maps.app.goo.gl" in url:
        try:
            # High-fidelity User Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, allow_redirects=True, timeout=5, headers=headers)
            url = response.url
            logger.info(f"Expanded Google Maps URL: {url}")
        except Exception as e:
            logger.error(f"Failed to expand Google Maps link: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to expand short link: {str(e)}"
            )

    # 2. Extract Coordinates using prioritized patterns
    
    # Pattern 1: High Precision Marker (!3dLAT!4dLON) - Often in 'data' params
    match_data = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
    if match_data:
        return float(match_data.group(1)), float(match_data.group(2))

    # Pattern 2: Viewport / Marker Context (@LAT,LON)
    match_at = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if match_at:
        return float(match_at.group(1)), float(match_at.group(2))

    # Pattern 3: Query Parameter (q=LAT,LON)
    match_q = re.search(r'[?&]q=([-+]?\d*\.\d+|\d+),([-+]?\d*\.\d+|\d+)', url)
    if match_q:
        return float(match_q.group(1)), float(match_q.group(2))

    # Pattern 4: Path coordinates (/LAT,LON)
    match_path = re.search(r'/([-+]?\d+\.\d+),([-+]?\d+\.\d+)', url)
    if match_path:
        return float(match_path.group(1)), float(match_path.group(2))

    logger.warning(f"Failed to parse coordinates from URL: {url}")
    raise ValueError("Invalid Google Maps URL. GPS data not found.")