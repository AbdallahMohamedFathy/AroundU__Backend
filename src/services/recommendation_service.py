"""
Recommendation Service – AroundU
=================================
Computes a weighted recommendation score for candidate places based on:
  - Rating quality  (Bayesian average)   → weight 0.5
  - Proximity       (reciprocal decay)   → weight 0.3
  - Popularity      (log-scaled favs)    → weight 0.2

All component scores are normalized to [0, 1].
"""

import math
import time
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.repositories.place_repository import PlaceRepository

logger = logging.getLogger(__name__)

# ─── Scoring Weights ─────────────────────────────────────────────
WEIGHT_RATING = 0.5
WEIGHT_DISTANCE = 0.3
WEIGHT_FAVORITE = 0.2

# ─── Bayesian Average Defaults ───────────────────────────────────
# m = minimum reviews before we trust the place's own average
BAYESIAN_MIN_REVIEWS = 10


# ═════════════════════════════════════════════════════════════════
#  Individual Score Components
# ═════════════════════════════════════════════════════════════════

def _bayesian_rating_score(
    avg_rating: float,
    review_count: int,
    global_avg: float,
    min_reviews: int = BAYESIAN_MIN_REVIEWS,
) -> float:
    """
    Bayesian average rating, normalized to [0, 1].

    Formula:
        weighted = (v / (v + m)) * R  +  (m / (v + m)) * C
    Where:
        v = review_count,  R = avg_rating,  C = global_avg,  m = min_reviews

    Result is divided by 5 to normalize to [0, 1].
    """
    v = review_count
    m = min_reviews
    R = avg_rating
    C = global_avg

    if v + m == 0:
        return C / 5.0

    weighted = (v / (v + m)) * R + (m / (v + m)) * C
    return min(weighted / 5.0, 1.0)


def _distance_score(distance_km: float) -> float:
    """
    Reciprocal decay: closer places score higher.

    Formula:  1 / (1 + distance_km)
    Result is in [0, 1] — a place at 0 km scores 1.0.
    """
    return 1.0 / (1.0 + max(distance_km, 0.0))


def _favorite_score(favorite_count: int, max_favorite_count: int) -> float:
    """
    Logarithmic normalization to reduce outlier dominance.

    Formula:  log(fav + 1) / log(max_fav + 1)
    Result is in [0, 1].
    """
    if max_favorite_count <= 0:
        return 0.0
    numerator = math.log(favorite_count + 1)
    denominator = math.log(max_favorite_count + 1)
    if denominator == 0:
        return 0.0
    return min(numerator / denominator, 1.0)


# ═════════════════════════════════════════════════════════════════
#  Composite Score
# ═════════════════════════════════════════════════════════════════

def _compute_score(
    candidate: dict,
    global_avg: float,
    max_fav: int,
) -> float:
    """Compute the final weighted recommendation score for a single candidate."""
    rs = _bayesian_rating_score(
        candidate["rating"],
        candidate["review_count"],
        global_avg,
    )
    ds = _distance_score(candidate["distance_km"])
    fs = _favorite_score(candidate["favorite_count"], max_fav)

    return round(WEIGHT_RATING * rs + WEIGHT_DISTANCE * ds + WEIGHT_FAVORITE * fs, 6)


# ═════════════════════════════════════════════════════════════════
#  Public API
# ═════════════════════════════════════════════════════════════════

def get_recommendations(
    session: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 10.0,
    category_id: Optional[int] = None,
    limit: int = 20,
    candidate_limit: int = 300,
) -> dict:
    """
    Main entry point — returns scored and sorted recommended places.

    Steps:
      1. Fetch up to `candidate_limit` nearest active places within `radius_km`.
      2. Fetch global rating stats for Bayesian prior.
      3. Score each candidate.
      4. Sort descending by score and return top `limit`.

    Returns a dict matching RecommendationListResponse schema.
    """
    start_time = time.perf_counter()

    repo = PlaceRepository(session)

    # ── 1. Candidate fetch ──────────────────────────────────────
    candidates = repo.get_recommendation_candidates(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        category_id=category_id,
        limit=candidate_limit,
    )

    total_candidates = len(candidates)

    if not candidates:
        logger.info(
            "Recommendation: 0 candidates found at (%.4f, %.4f) r=%.1fkm",
            latitude, longitude, radius_km,
        )
        return {
            "total_candidates": 0,
            "returned": 0,
            "radius_km": radius_km,
            "items": [],
        }

    # ── 2. Global stats (Bayesian prior) ────────────────────────
    stats = repo.get_global_rating_stats()
    global_avg = stats["global_avg_rating"]

    # ── 3. Max favorites in candidate set ───────────────────────
    max_fav = max(c["favorite_count"] for c in candidates)

    # ── 4. Score each candidate ─────────────────────────────────
    for c in candidates:
        c["score"] = _compute_score(c, global_avg, max_fav)

    # ── 5. Sort by score descending and trim ────────────────────
    candidates.sort(key=lambda c: c["score"], reverse=True)
    top_results = candidates[:limit]

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "Recommendation: %d candidates → top %d returned in %.1fms | (%.4f, %.4f) r=%.1fkm",
        total_candidates, len(top_results), elapsed_ms,
        latitude, longitude, radius_km,
    )

    # ── 6. Format response ──────────────────────────────────────
    items = [
        {
            "id": c["id"],
            "name": c["name"],
            "description": c["description"],
            "address": c["address"],
            "category": c["category"],
            "latitude": c["latitude"],
            "longitude": c["longitude"],
            "distance_km": round(c["distance_km"], 2),
            "avg_rating": round(c["rating"], 2),
            "review_count": c["review_count"],
            "favorite_count": c["favorite_count"],
            "score": round(c["score"], 4),
        }
        for c in top_results
    ]

    return {
        "total_candidates": total_candidates,
        "returned": len(items),
        "radius_km": radius_km,
        "items": items,
    }
