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
            base_url="https://mazenmaher26-aroundu-location-logic.hf.space",
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
    
    async def get_opportunities(self, points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        POST /opportunities

        AI requires both "places" and "visits" keys in the payload to properly
        validate even if they contain the same data points.
        """
        valid_points = [
            {
                "lat": float(p["lat"]),
                "lon": float(p["lon"]),
                "cluster": int(p["cluster"]),
                "category": str(p["category"]),
                "district": str(p["district"]),
            }
            for p in points
            if p.get("lat") is not None
            and p.get("lon") is not None
            and p.get("cluster") is not None
            and p.get("category")
            and p.get("district")
            and -90 < float(p["lat"]) < 90
            and -180 < float(p["lon"]) < 180
        ]

        if not valid_points:
            return []

        # 🔥 Unified payload with both keys to satisfy schema requirements
        payload = {
            "places": valid_points,
            "visits": valid_points
        }

        logger.info(f"[AILocationService] POST /opportunities — {len(valid_points)} points")

        res = await self._request_with_retry(
            "POST", "/opportunities", json=payload
        )

        if not res:
            return []

        if isinstance(res, dict):
            return res.get("opportunities", res.get("places", []))

        if isinstance(res, list):
            return res

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

    # ------------------------------------------------------------------
    # Additional logic endpoints provided by AI Team
    # ------------------------------------------------------------------

    async def get_health(self) -> Dict[str, Any]:
        """GET /health"""
        res = await self._request_with_retry("GET", "/health")
        return res if isinstance(res, dict) else {}

    async def get_active_visitors(self, visits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """POST /active-visitors"""
        if not visits: return []
        payload = {"visits": visits}
        res = await self._request_with_retry("POST", "/active-visitors", json=payload)
        if isinstance(res, dict): return res.get("visitors", res.get("data", res.get("active_visitors", [])))
        return res if isinstance(res, list) else []

    async def get_peak_hour(self, visits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """POST /peak-hour"""
        if not visits: return {}
        payload = {"visits": visits}
        res = await self._request_with_retry("POST", "/peak-hour", json=payload)
        return res if isinstance(res, dict) else {}

    async def get_owner_summary(self, visits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """POST /owner-summary"""
        if not visits: return {}
        payload = {"visits": visits}
        res = await self._request_with_retry("POST", "/owner-summary", json=payload)
        return res if isinstance(res, dict) else {}

    async def get_admin_summary(self, visits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """POST /admin-summary"""
        if not visits: return {}
        payload = {"visits": visits}
        res = await self._request_with_retry("POST", "/admin-summary", json=payload)
        return res if isinstance(res, dict) else {}


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

ai_location_service = AILocationService()
