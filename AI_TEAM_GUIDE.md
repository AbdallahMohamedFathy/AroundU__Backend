# 🤖 AroundU - AI Team Integration Guide

Welcome to the **AroundU AI Data Gateway**! 
This document provides everything you need to know to extract sanitized, structured data from the AroundU backend to train your Machine Learning and Recommendation models.

---

## 🔐 1. Authentication & Base URL

To ensure data privacy and security, all AI endpoints are protected by an API Key. 

- **Base URL (Production):** `https://aroundubackend-production.up.railway.app`
- **Authentication Header:** `X-API-Key`
- **Your API Key:** *(Please request your secure API Key from the Backend Admin)*

All requests must include the `X-API-Key` in the HTTP headers.

---

## 📡 2. Available Endpoints

The AI Gateway provides read-only access to necessary data. All endpoints return a standard JSON response.

### A. User Interactions (For Collaborative Filtering)
**Endpoint:** `GET /api/v1/ai/data/interactions`

Returns a list of interactions users have made with places (e.g., visits, saves, directions, calls). This is the primary dataset for building Collaborative Filtering recommendation engines.

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Items per page (max: 100)

**Response Format:**
```json
{
  "data": [
    {
      "user_id": "1",
      "event_type": "visit",  // "visit", "save", "direction", etc.
      "place_id": "32",
      "rating_value": null,
      "timestamp": "2026-05-01T10:00:00Z"
    }
  ],
  "meta": { "limit": 100, "skip": 0 }
}
```

### B. Places Metadata (For Content-Based Filtering)
**Endpoint:** `GET /api/v1/ai/data/places`

Returns metadata about places including categories, coordinates, and aggregate ratings. Useful for Content-Based Filtering or Context-Aware recommendations.

**Query Parameters:**
- `skip` (int): Pagination offset (default: 0)
- `limit` (int): Items per page (max: 100)

**Response Format:**
```json
{
  "data": [
    {
      "place_id": "32",
      "name": "Bolivar",
      "category": "Restaurant & Café",
      "rating": 4.5,
      "review_count": 120,
      "lat": 29.067624,
      "lng": 31.110061
    }
  ],
  "meta": { "limit": 100, "skip": 0 }
}
```

### C. Live Analytics (For Trends & Insights)
**Endpoint:** `GET /api/v1/ai/data/analytics`

Returns dynamically calculated analytics, such as the highest-rated places, most visited places, and currently trending categories.

**Response Format:**
```json
{
  "top_rated_places": [ ... ],
  "most_visited_places": [ ... ],
  "trending_categories": ["Restaurant & Café", "Cafe"]
}
```

---

## 🧑‍💻 3. Python Integration Script (Ready to use)

You don't need to manually test these in Postman or Swagger. You can copy the following Python script directly into your **Jupyter Notebook** or ETL pipeline to fetch all data and convert it into `pandas` DataFrames ready for training.

```python
import requests
import pandas as pd
import time

# --- CONFIGURATION ---
BASE_URL = "https://aroundubackend-production.up.railway.app/api/v1/ai/data"
API_KEY = "YOUR_API_KEY_HERE" # Replace with the key provided by the Backend team

HEADERS = {
    "X-API-Key": API_KEY,
    "Accept": "application/json"
}

def fetch_paginated_data(endpoint_name):
    """Fetches all data from a paginated AI Gateway endpoint."""
    print(f"Fetching data from {endpoint_name}...")
    all_data = []
    skip = 0
    limit = 100
    
    while True:
        url = f"{BASE_URL}/{endpoint_name}?skip={skip}&limit={limit}"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 429:
            print("Rate limit reached. Waiting for 60 seconds...")
            time.sleep(60)
            continue
            
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            break
            
        data_chunk = response.json().get("data", [])
        if not data_chunk:
            break # No more data to fetch
            
        all_data.extend(data_chunk)
        skip += limit
        
    print(f"✅ Total records loaded from {endpoint_name}: {len(all_data)}")
    return pd.DataFrame(all_data)

# ==========================================
# 1. Load Data
# ==========================================

# Dataset 1: User Interactions (For User-Item Matrix)
df_interactions = fetch_paginated_data("interactions")
display(df_interactions.head())

# Dataset 2: Places Metadata (For Content Features)
df_places = fetch_paginated_data("places")
display(df_places.head())

# ==========================================
# 2. Example: Merging Data for Training
# ==========================================
if not df_interactions.empty and not df_places.empty:
    # Merge interactions with place metadata based on place_id
    df_merged = pd.merge(df_interactions, df_places, on="place_id", how="left")
    display(df_merged.head())
    
    # Save to CSV for offline training
    # df_merged.to_csv("aroundu_training_data.csv", index=False)
```

## ⚠️ Notes for AI Engineers
- **Rate Limiting:** The API is rate-limited to 20 requests per minute to protect database performance. The Python script above automatically handles rate limits (`429` status code) by sleeping and retrying.
- **Sanitization:** Sensitive user data (like passwords, emails, and exact names) are omitted from these endpoints for privacy. Users are identified strictly by anonymized `user_id` strings.
