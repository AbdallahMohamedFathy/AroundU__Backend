import httpx
from typing import List, Dict
from ai_service.core.config import settings

class RecommendationService:
    def __init__(self):
        self.backend_url = settings.BACKEND_URL

    async def get_user_behavior_data(self, user_id: int) -> Dict:
        """Fetch user favorites, reviews, and search history from backend."""
        async with httpx.AsyncClient() as client:
            try:
                # In a real microservice, we would have dedicated endpoints for these
                # For now, we assume the backend provides a summary endpoint or we fetch multiple
                favs_resp = await client.get(f"{self.backend_url}/favorites/user/{user_id}")
                reviews_resp = await client.get(f"{self.backend_url}/reviews/user/{user_id}")
                
                return {
                    "favorites": favs_resp.json() if favs_resp.status_code == 200 else [],
                    "reviews": reviews_resp.json() if reviews_resp.status_code == 200 else []
                }
            except Exception as e:
                print(f"Error fetching user data: {e}")
                return {"favorites": [], "reviews": []}

    async def get_recommendations(self, user_id: int) -> List[Dict]:
        """Simple content-based filtering logic."""
        user_data = await self.get_user_behavior_data(user_id)
        
        # Identify categories user likes from favorites and high-rated reviews
        liked_category_ids = set()
        for fav in user_data["favorites"]:
            # Extract category from place if present
            if "place" in fav and "category_id" in fav["place"]:
                liked_category_ids.add(fav["place"]["category_id"])
        
        for review in user_data["reviews"]:
            if review.get("rating", 0) >= 4:
                if "place" in review and "category_id" in review["place"]:
                    liked_category_ids.add(review["place"]["category_id"])

        # Fetch places in those categories from backend
        all_recommended_places = []
        async with httpx.AsyncClient() as client:
            for cat_id in liked_category_ids:
                resp = await client.get(f"{self.backend_url}/places/?category_id={cat_id}")
                if resp.status_code == 200:
                    places = resp.json().get("items", [])
                    all_recommended_places.extend(places)

        # Remove duplicates and return
        seen_ids = set()
        unique_places = []
        for p in all_recommended_places:
            if p["id"] not in seen_ids:
                unique_places.append(p)
                seen_ids.add(p["id"])
                
        return unique_places[:10]  # Return top 10

recommendation_service = RecommendationService()
