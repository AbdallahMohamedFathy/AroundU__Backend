import requests
import re
from fastapi import HTTPException, status


def extract_coordinates_from_google_maps(url: str):
    
    # expand short links
    if "maps.app.goo.gl" in url:
        try:
            response = requests.get(url, allow_redirects=True, timeout=5)
            url = response.url
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to expand short link: {str(e)}"
            )

    # pattern for @lat,long
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)

    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return lat, lon

    # pattern for ?q=lat,long
    match = re.search(r'q=(-?\d+\.\d+),(-?\d+\.\d+)', url)

    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        return lat, lon

    raise ValueError("Invalid Google Maps URL")