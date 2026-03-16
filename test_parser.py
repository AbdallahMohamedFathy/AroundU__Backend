from src.utils.location_parser import extract_coordinates

test_links = [
    # Example 1: Standard Browser URL
    "https://www.google.com/maps/place/%D9%85%D8%B7%D8%B9%D9%85+%2B%D8%B3%D9%84%D8%B7%D8%B7%D8%A7%D9%86+%D8%A7%D9%84%D8%B4%D8%A7%D9%85+%D8%A8%D9%86%D9%8A+%D8%B3%D9%88%D9%8A%D9%81%D2%AD/@29.0679935,31.1095432,17z",
    
    # Example 2: Query param q
    "https://maps.google.com/?q=29.0679935,31.1095432",
    
    # Example 3: Data parameter !3d
    "https://www.google.com/maps/place/Sultan+Al-Sham/@29.0680062,31.1095087,17z/data=!3m1!4b1!4m6!3m5!1s0x145a27003493da75:0x480f538b4f293dd0!8m2!3d29.0680062!4d31.1095087!16s%2Fg%2F11y3xtwp8z",
    
    # Example 4: Consent Redirect
    "https://consent.google.com/ml?continue=https://www.google.com/maps/place/%25D9%2585%25D8%25B7%25D8%25B9%25D9%2585%2B%25D8%25B3%25D9%2584%25D8%25B7%25D8%25A7%25D9%2586%2B%25D8%25A7%25D9%2584%25D8%25B4%25D8%25A7%25D9%2585%2B%25D8%25A8%25D9%2586%25D9%258A%2B%25D8%25B3%25D9%2588%25D9%258A%25D9%2581%25E2%2580%25AD/@29.0679935,31.1095432,17z"
]

for i, link in enumerate(test_links):
    print(f"Testing Link {i+1}:")
    coords = extract_coordinates(link)
    if coords:
        print(f"  Result: LAT={coords[0]}, LON={coords[1]}")
    else:
        print("  Result: FAILED")
