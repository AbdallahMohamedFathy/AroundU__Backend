import re
from fastapi import HTTPException, status

def extract_coordinates_from_google_maps(url: str):
    """
    Extracts latitude and longitude from various Google Maps URL formats.
    Supported formats:
    - https://maps.google.com/?q=29.0661,31.0994
    - https://www.google.com/maps/@29.0661,31.0994,17z
    - https://www.google.com/maps/place/.../@29.0661,31.0994,17z...
    """
    if not url:
        return None, None

    # Format 1: ?q=LAT,LON
    match_q = re.search(r'[?&]q=([-+]?\d*\.\d+|\d+),([-+]?\d*\.\d+|\d+)', url)
    if match_q:
        return float(match_q.group(1)), float(match_q.group(2))

    # Format 2: /@LAT,LON,z
    match_at = re.search(r'@([-+]?\d*\.\d+|\d+),([-+]?\d*\.\d+|\d+)', url)
    if match_at:
        return float(match_at.group(1)), float(match_at.group(2))

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid Google Maps location link. Please provide a link containing coordinates."
    )
