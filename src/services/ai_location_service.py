"""
ai_location_service.py
-----------------------
Client for the AroundU Location Clustering microservice.

Endpoint payload contracts (as specified by the AI team):
  POST /predict       → {"lat": float, "lon": float}
  POST /heatmap       → {"visits": [{"lat", "lon", "cluster"}, ...]}
  POST /opportunities → {"places": [{"lat","lon","cluster","category","district"}, ...]}
  GET  /clusters      → (no body)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.core.logger import logger
from src.services.base_ai import BaseAIService


class AILocationService(BaseAIService):
    """Client for the AroundU Location Clustering microservice."""

    def __init__(self) -> None:
        super().__init__(
            service_name="AI Location Service",
            base_url="https://mazenmaher26-aroundu-location-clustering.hf.space",
            timeout=20.0,
            max_retries=3,
        )

    # ------------------------------------------------------------------
    # predict_cluster
    # ------------------------------------------------------------------

    async def predict_cluster(
        self, lat: float, lon: float
    ) -> Optional[Dict[str, Any]]:
        """Predict the cluster ID for a single coordinate pair."""
        payload = {"lat": lat, "lon": lon}
        logger.info(f"[AILocationService] POST /predict — payload: {payload}")
        return await self._request_with_retry("POST", "/predict", json=payload)

    # ------------------------------------------------------------------
    # get_heatmap
    # ------------------------------------------------------------------

    async def get_heatmap(
        self, points: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        POST /heatmap

        AI expects: {"visits": [{"lat", "lon", "cluster"}, ...]}

        Filters out any point missing lat, lon, or cluster so the AI never
        receives a 422-triggering null field.
        """
        valid_points = [
            {
                "lat":     float(p["lat"]),
                "lon":     float(p["lon"]),
                "cluster": int(p["cluster"]),
            }
            for p in points
            if p.get("lat") is not None
            and p.get("lon") is not None
            and p.get("cluster") is not None
        ]

        if not valid_points:
            logger.info("[AILocationService] get_heatmap: no valid points, skipping.")
            return []

        payload = {"visits": valid_points}   # AI key is "visits", NOT "places"
        logger.info(
            f"[AILocationService] POST /heatmap — "
            f"{len(valid_points)} points. Payload preview: {payload!r:.500}"
        )

        data = await self._request_with_retry("POST", "/heatmap", json=payload)

        if not data:
            return []
        if isinstance(data, dict):
            return data.get("hotspots", data.get("heatmap", []))
        if isinstance(data, list):
            return data

        logger.warning(f"[AILocationService] Unexpected /heatmap response type: {type(data)}")
        return []

    # ------------------------------------------------------------------
    # get_opportunities
    # ------------------------------------------------------------------

    
        
    async def get_opportunities(
        self, points: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        POST /opportunities

        AI expects: {"places": [{"lat","lon","cluster","category","district"}, ...]}

        All five fields MUST be present and non-null.
        """
        valid_points = []

        for p in points:
            try:
                lat = p.get("lat")
                lon = p.get("lon")
                cluster = p.get("cluster")
                category = p.get("category")
                district = p.get("district")

                # 🔥 Validation حقيقي
                if (
                    lat is None or lon is None or cluster is None
                    or not category or not district
                ):
                    continue

                lat = float(lat)
                lon = float(lon)
                cluster = int(cluster)

                # 🔥 Range check (مهم جدًا)
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    continue

                valid_points.append({
                    "lat": lat,
                    "lon": lon,
                    "cluster": cluster,
                    "category": str(category).strip(),
                    "district": str(district).strip(),
                })

            except Exception as e:
                logger.warning(f"[AI] Skipping bad point: {p} — {e}")
                continue

        if not valid_points:
            logger.info("[AILocationService] No valid points → skip AI call")
            return []

        payload = {"visits": valid_points}

        logger.info(
            f"[AILocationService] POST /opportunities — {len(valid_points)} points"
        )

        data = await self._request_with_retry(
            "POST",
            "/opportunities",
            json=payload
        )

        if not data:
            return []

        if isinstance(data, dict):
            return data.get("opportunities", [])

        if isinstance(data, list):
            return data

        logger.warning(f"[AILocationService] Unexpected response type: {type(data)}")
        return []
    # ------------------------------------------------------------------
    # get_clusters
    # ------------------------------------------------------------------

    async def get_clusters(self) -> List[Dict[str, Any]]:
        """GET /clusters — returns all known cluster definitions."""
        logger.info("[AILocationService] GET /clusters")
        data = await self._request_with_retry("GET", "/clusters")

        if not data:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("clusters", [])
        return []


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

ai_location_service = AILocationService()
