"""
anomaly_helpers.py
------------------
Data preparation utilities for the AroundU anomaly detection pipeline.

These helpers clean and shape raw Interaction ORM objects into the exact
payloads expected by each AI endpoint, enforcing a strict validation layer
so the AI service never receives incomplete or invalid records.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from src.core.logger import logger


# ---------------------------------------------------------------------------
# Internal validation helper
# ---------------------------------------------------------------------------

def _is_valid_visit(interaction: Any) -> bool:
    """Return True only if the interaction is a full, clean visit record."""
    return (
        interaction.user_id is not None
        and interaction.user_lat is not None
        and interaction.user_lon is not None
        and interaction.cluster_id is not None
        and interaction.created_at is not None
    )


def _to_visit_dict(interaction: Any) -> Dict[str, Any]:
    """Serialize a valid Interaction ORM object to the AI visit schema."""
    return {
        "user_id": interaction.user_id,
        "place_id": interaction.place_id,
        "user_lat": float(interaction.user_lat),
        "user_lon": float(interaction.user_lon),
        "visited_at": interaction.created_at.isoformat(),
        "cluster": int(interaction.cluster_id),
    }


# ---------------------------------------------------------------------------
# TASK 1 — Public preparation functions
# ---------------------------------------------------------------------------

def prepare_user_visits(interactions: List[Any]) -> List[Dict[str, Any]]:
    """
    Build a clean visit list for the AI /detect endpoint.

    Filters out:
    - Interactions with a None user_id  (anonymous / non-human)
    - Missing coordinates
    - Missing cluster assignment
    - Missing timestamp

    Returns list ready for: {"visits": <result>}
    """
    valid = [i for i in interactions if _is_valid_visit(i)]
    dropped = len(interactions) - len(valid)

    if dropped:
        logger.warning(
            f"[anomaly_helpers] Dropped {dropped}/{len(interactions)} "
            "interactions due to missing fields."
        )

    result = [_to_visit_dict(i) for i in valid]
    logger.info(f"[anomaly_helpers] prepare_user_visits → {len(result)} valid visits")
    return result


def prepare_place_metrics(interactions: List[Any]) -> List[Dict[str, Any]]:
    """
    Aggregate interaction metrics for a place and return them in the flat
    list format expected by the AI /summary endpoint.

    Format: [{"metric_name": str, "value": int}, ...]
    """
    visits = [i for i in interactions if i.type == "visit"]
    unique_users = {i.user_id for i in visits if i.user_id is not None}

    # Visits per hour (group by hour bucket)
    hour_buckets: Dict[str, int] = defaultdict(int)
    for v in visits:
        if v.created_at:
            bucket = v.created_at.strftime("%Y-%m-%dT%H")
            hour_buckets[bucket] += 1

    max_visits_per_hour = max(hour_buckets.values()) if hour_buckets else 0

    metrics = [
        {"metric_name": "visits", "value": len(visits)},
        {"metric_name": "unique_users", "value": len(unique_users)},
        {"metric_name": "max_visits_per_hour", "value": max_visits_per_hour},
    ]

    logger.info(
        f"[anomaly_helpers] prepare_place_metrics → visits={len(visits)}, "
        f"unique_users={len(unique_users)}, max_vph={max_visits_per_hour}"
    )
    return metrics


def prepare_district_data(interactions: List[Any]) -> List[Dict[str, Any]]:
    """
    Group valid interactions by cluster (district proxy) so the AI can
    detect District Spike and Dead Zone anomalies.

    Returns a list of per-cluster visit records, each shaped as a normal
    visit dict (reuses the same schema as /detect).
    """
    valid = [i for i in interactions if _is_valid_visit(i)]

    # Build cluster → visits mapping for logging / future use
    by_cluster: Dict[int, int] = defaultdict(int)
    for i in valid:
        by_cluster[i.cluster_id] += 1

    logger.info(
        f"[anomaly_helpers] prepare_district_data → "
        f"{len(valid)} valid visits across {len(by_cluster)} clusters: {dict(by_cluster)}"
    )

    return [_to_visit_dict(i) for i in valid]


def prepare_place_anomaly_payload(
    place_id: int, interactions: List[Any]
) -> Dict[str, Any]:
    """
    Build the payload for the AI /place-anomalies endpoint.

    Format: {"place_id": int, "visits": [...]}
    """
    visits = prepare_user_visits(interactions)
    payload = {"place_id": place_id, "visits": visits}
    logger.info(
        f"[anomaly_helpers] prepare_place_anomaly_payload → "
        f"place_id={place_id}, visits={len(visits)}"
    )
    return payload
