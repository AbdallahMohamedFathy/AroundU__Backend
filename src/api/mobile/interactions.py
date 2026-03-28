"""
interactions.py  (Mobile API)
------------------------------
Records user interactions with places.

Real-time anomaly detection strategy
-------------------------------------
For VISIT type interactions with coordinates, we fire two lightweight checks
in the background WITHOUT blocking the API response:

  • Impossible Travel  — did this user teleport since their last visit?
  • GPS Spoofing       — are the coordinates physically plausible?

These are the only anomaly types that benefit from per-request context.
All other anomalies (Bot Behavior, Traffic Spike, etc.) are cheaper to
detect in batch when the dashboard loads.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, status

from src.core.dependencies import get_uow, get_current_user_optional
from src.models.interaction import Interaction
from src.models.user import User
from src.schemas.interaction import InteractionCreate, InteractionResponse
from src.services.ai_location_service import ai_location_service
from src.core.logger import logger

router = APIRouter()


# ---------------------------------------------------------------------------
# Background task: real-time anomaly detection for a single new visit
# ---------------------------------------------------------------------------

async def _run_realtime_anomaly_check(visit_payload: dict) -> None:
    """
    Fire-and-forget coroutine.

    Sends a single-visit payload to the AI /detect endpoint and logs any
    Impossible Travel or GPS Spoofing anomalies found.  Never raises —
    exceptions are caught and logged so the main request is never affected.

    Only called when the visit has all required fields (user_id, lat, lon,
    cluster_id, visited_at) as validated at the call site.
    """
    try:
        from src.services.anomaly_service import ai_anomaly_service

        logger.info(
            f"[realtime_anomaly] Checking visit for user_id={visit_payload.get('user_id')}, "
            f"place_id={visit_payload.get('place_id')}"
        )

        anomalies = await ai_anomaly_service.detect_anomalies([visit_payload])

        realtime_types = {"impossible_travel", "gps_spoofing"}
        flagged = [
            a for a in anomalies
            if isinstance(a, dict)
            and str(a.get("anomaly_type", "")).lower().replace(" ", "_") in realtime_types
        ]

        if flagged:
            logger.warning(
                f"[realtime_anomaly] FLAGGED {len(flagged)} anomaly(ies) for "
                f"user_id={visit_payload.get('user_id')}: {flagged}"
            )
        else:
            logger.info(
                f"[realtime_anomaly] No real-time anomalies for "
                f"user_id={visit_payload.get('user_id')}"
            )

    except Exception as exc:  # noqa: BLE001
        logger.error(f"[realtime_anomaly] Background check failed: {exc}", exc_info=True)


# ---------------------------------------------------------------------------
# POST /{place_id}/interactions
# ---------------------------------------------------------------------------

@router.post(
    "/{place_id}/interactions",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_interaction(
    place_id: int,
    interaction_in: InteractionCreate,
    uow=Depends(get_uow),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Record a user interaction with a place.

    • If type == 'visit' and coordinates are present → predict cluster via AI.
    • If the visit is attributable to a logged-in user with full data →
      fire a real-time anomaly check in the background (non-blocking).
    """
    # ── 1. Cluster prediction (visit + coordinates required) ──────────────
    cluster_id: Optional[int] = None

    if (
        interaction_in.type == "visit"
        and interaction_in.user_lat is not None
        and interaction_in.user_lon is not None
    ):
        try:
            cluster_data = await ai_location_service.predict_cluster(
                interaction_in.user_lat, interaction_in.user_lon
            )
            if cluster_data:
                cluster_id = cluster_data.get("cluster")
        except Exception as exc:
            logger.warning(f"[record_interaction] Cluster prediction failed: {exc}")

    # ── 2. Persist interaction ────────────────────────────────────────────
    with uow:
        interaction = Interaction(
            place_id=place_id,
            user_id=current_user.id if current_user else None,
            type=interaction_in.type,
            user_lat=interaction_in.user_lat,
            user_lon=interaction_in.user_lon,
            cluster_id=cluster_id,
        )
        uow.interaction_repository.create(interaction)
        uow.commit()

        # Snapshot values before the session closes
        saved_id         = interaction.id
        saved_user_id    = interaction.user_id
        saved_place_id   = interaction.place_id
        saved_lat        = interaction.user_lat
        saved_lon        = interaction.user_lon
        saved_cluster_id = interaction.cluster_id
        saved_type       = interaction.type
        saved_created_at = interaction.created_at

    # ── 3. Real-time anomaly check (non-blocking, best-effort) ───────────
    #    Only fire if all required AI fields are available
    if (
        interaction_in.type == "visit"
        and current_user is not None
        and saved_lat is not None
        and saved_lon is not None
        and saved_cluster_id is not None
        and saved_created_at is not None
    ):
        visit_payload = {
            "user_id":    saved_user_id,
            "place_id":   saved_place_id,
            "user_lat":   float(saved_lat),
            "user_lon":   float(saved_lon),
            "visited_at": saved_created_at.isoformat(),
            "cluster":    int(saved_cluster_id),
        }
        # Fire and forget — do NOT await
        asyncio.create_task(_run_realtime_anomaly_check(visit_payload))

    # ── 4. Return persisted interaction ───────────────────────────────────
    return InteractionResponse(
        id=saved_id,
        place_id=saved_place_id,
        user_id=saved_user_id,
        type=saved_type,
        user_lat=saved_lat,
        user_lon=saved_lon,
        cluster_id=saved_cluster_id,
        created_at=saved_created_at,
    )
