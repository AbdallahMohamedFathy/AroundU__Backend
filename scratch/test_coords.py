import requests
import re

def extract_coordinates(url):
    if not url: return None, None
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        session = requests.Session()
        res = session.get(url, allow_redirects=True, headers=headers, timeout=10.0)
        resolved_url = res.url
        decoded_url = requests.utils.unquote(resolved_url)
        
        print(f"Resolved URL: {resolved_url}")
        
        patterns = [
            r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)',
            r'@(-?\d+\.\d+),(-?\d+\.\d+)',
            r'[?&]q=([-+]?\d*\.\d+|\d+),([-+]?\d*\.\d+|\d+)',
            r'/([-+]?\d+\.\d+),([-+]?\d+\.\d+)',
        ]

        for text in [resolved_url, decoded_url]:
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return float(match.group(1)), float(match.group(2))
    except Exception as e:
        print(f"Error: {e}")
    return None, None

url = "https://maps.app.goo.gl/pzucpd38weGdHLyg7"
lat, lon = extract_coordinates(url)
print(f"Result: {lat}, {lon}")
