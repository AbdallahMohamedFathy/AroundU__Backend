import requests
import re
from fastapi import HTTPException, status


def extract_coordinates_from_google_maps(url: str):
    
    # expand short links
    if "maps.app.goo.gl" in url:
        response = requests.get(url, allow_redirects=True)
        url = response.url

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