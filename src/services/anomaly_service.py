"""
anomaly_service.py
------------------
AI Anomaly Detection service for AroundU.

Wraps the HuggingFace-hosted anomaly detection microservice.
Each method sends a precisely-shaped payload and unwraps the response
according to the AI team's endpoint specifications.

Anomaly categories supported:
  USER     → Bot Behavior, GPS Spoofing, Impossible Travel
  PLACE    → Traffic Spike, Sudden Drop, Unusual Hours
  DISTRICT → District Spike, Dead Zone
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.core.logger import logger
from src.services.base_ai import BaseAIService


class AIAnomalyService(BaseAIService):
    """Client for the AroundU Anomaly Detection microservice."""

    def __init__(self) -> None:
        super().__init__(
            service_name="AI Anomaly Service",
            base_url="https://mazenmaher26-aroundu-anomaly-detection.hf.space",
            timeout=30.0,   # anomaly detection can be compute-intensive
            max_retries=3,
        )

    # ------------------------------------------------------------------
    # detect_anomalies — covers USER + PLACE anomalies
    # ------------------------------------------------------------------

    async def detect_anomalies(
        self, visits: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        POST /detect

        Detects all anomaly types from raw visit data.
        Called by the backend on each incoming visit (real-time path)
        or in batch when the dashboard loads.

        Expected payload:
        {
          "visits": [
            {
              "user_id":    int,
              "place_id":   int,
              "user_lat":   float,
              "user_lon":   float,
              "visited_at": ISO-8601 string,
              "cluster":    int
            },
            ...
          ]
        }

        Returns: list of anomaly dicts, each containing:
          - anomaly_type, severity, category, details
        """
        if not visits:
            logger.info("[AIAnomalyService] detect_anomalies: empty visit list, skipping.")
            return []

        payload = {"visits": visits}
        logger.info(
            f"[AIAnomalyService] POST /detect — sending {len(visits)} visits. "
            f"Payload preview: {payload!r:.500}"
        )

        res = await self._request_with_retry("POST", "/detect", json=payload)

        if not res:
            return []

        # Unwrap: AI may return {"anomalies": [...]} or the list directly
        if isinstance(res, dict):
            return res.get("anomalies", res.get("visits", []))
        if isinstance(res, list):
            return res

        logger.warning(f"[AIAnomalyService] Unexpected /detect response type: {type(res)}")
        return []

    # ------------------------------------------------------------------
    # get_place_anomalies — Place-scoped anomaly filtering
    # ------------------------------------------------------------------

    async def get_place_anomalies(
        self, place_id: int, visits: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        # 🔥 1. detect الأول
        anomalies = await self.detect_anomalies(visits)

        if not anomalies:
            logger.info("[AIAnomalyService] No anomalies detected → skip place-anomalies")
            return []

        # 🔥 2. ابعت anomalies مش visits
        payload = {
            "place_id": place_id,
            "anomalies": anomalies
        }

        logger.info(
            f"[AIAnomalyService] POST /place-anomalies — "
            f"place_id={place_id}, anomalies={len(anomalies)}"
        )

        res = await self._request_with_retry(
            "POST", "/place-anomalies", json=payload
        )

        if not res:
            return []

        if isinstance(res, dict):
            return res.get("anomalies", [])

        if isinstance(res, list):
            return res

        logger.warning(f"[AIAnomalyService] Unexpected response type: {type(res)}")
        return []
    # ------------------------------------------------------------------
    # get_summary — Aggregated anomaly statistics
    # ------------------------------------------------------------------

    async def get_summary(
        self, metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        POST /summary

        Returns aggregated anomaly statistics for admin / dashboard.
        Used by the admin dashboard to show which areas have the most anomalies.

        Expected payload (flat metric list):
        [
          {"metric_name": "visits",           "value": int},
          {"metric_name": "unique_users",     "value": int},
          {"metric_name": "max_visits_per_hour", "value": int}
        ]
        """
        if not metrics:
            logger.info("[AIAnomalyService] get_summary: empty metrics, skipping.")
            return {}

        logger.info(
            f"[AIAnomalyService] POST /summary — {len(metrics)} metrics. "
            f"Payload: {metrics!r}"
        )

        res = await self._request_with_retry("POST", "/summary", json=metrics)
        return res if isinstance(res, dict) and res else {}

    # ------------------------------------------------------------------
    # get_anomaly_summary — District-level aggregation for admin
    # ------------------------------------------------------------------

    async def get_anomaly_summary(
        self, visits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Convenience wrapper: detects anomalies and then fetches a summary.

        Used by GET /api/admin/anomalies/summary to produce a district-wide
        intelligence report that highlights District Spike / Dead Zone
        anomalies alongside Place and User anomalies.
        """
        anomalies = await self.detect_anomalies(visits)
        if not anomalies:
            return {
                "total_anomalies": 0,
                "urgent_anomalies": 0,
                "summary": "No anomalies detected.",
                "details": [],
            }

        urgent = sum(
            1 for a in anomalies
            if isinstance(a, dict) and str(a.get("severity", "")).lower() == "high"
        )

        return {
            "total_anomalies": len(anomalies),
            "urgent_anomalies": urgent,
            "summary": f"{len(anomalies)} anomalies detected, {urgent} high severity.",
            "details": anomalies,
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

ai_anomaly_service = AIAnomalyService()
