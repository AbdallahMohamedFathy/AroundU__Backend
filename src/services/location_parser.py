import requests
import re
from fastapi import HTTPException, status

def extract_coordinates_from_google_maps(url: str):
    """
    Extracts latitude and longitude from various Google Maps URL formats.
    Supports short links (maps.app.goo.gl) and various path/query params.
    """
    if not url:
        return None, None

    # 1. Expand short links
    if "maps.app.goo.gl" in url:
        try:
            # We use a user-agent to avoid being blocked during expansion
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, allow_redirects=True, timeout=5, headers=headers)
            url = response.url
            print(f"DEBUG: Expanded URL: {url}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to expand short link: {str(e)}"
            )

    # 2. Try various regex patterns to find coordinates
    
    # Pattern A: @LAT,LON (Standard expanded format)
    match_at = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if match_at:
        return float(match_at.group(1)), float(match_at.group(2))

    # Pattern B: q=LAT,LON (Standard search format)
    match_q = re.search(r'[?&]q=([-+]?\d*\.\d+|\d+),([-+]?\d*\.\d+|\d+)', url)
    if match_q:
        return float(match_q.group(1)), float(match_q.group(2))

    # Pattern C: /LAT,LON/ (Found in some mobile or place-specific URLs)
    match_path = re.search(r'/([-+]?\d+\.\d+),([-+]?\d+\.\d+)', url)
    if match_path:
        return float(match_path.group(1)), float(match_path.group(2))

    # 3. If all fails, log and raise
    print(f"DEBUG: Parsing failed for URL: {url}")
    raise ValueError(f"Invalid Google Maps URL. GPS data not found.")