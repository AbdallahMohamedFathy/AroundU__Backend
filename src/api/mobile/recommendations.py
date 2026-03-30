"""
GET /api/mobile/recommendations
================================
Returns scored and ranked place recommendations based on user location.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.logger import logger
from src.core.exceptions import APIException
from src.schemas.recommendation import RecommendationListResponse
from src.services import recommendation_service

router = APIRouter()


@router.get(
    "/",
    response_model=RecommendationListResponse,
    summary="Get personalized place recommendations",
    description=(
        "Returns nearby places ranked by a composite score: "
        "50% rating quality (Bayesian), 30% proximity, 20% popularity."
    ),
)
def get_recommendations(
    lat: float = Query(
        ...,
        ge=-90,
        le=90,
        description="User latitude",
        examples=[30.0444],
    ),
    lng: float = Query(
        ...,
        ge=-180,
        le=180,
        description="User longitude",
        examples=[31.2357],
    ),
    radius_km: float = Query(
        10.0,
        ge=0.5,
        le=50.0,
        description="Search radius in kilometers (0.5 – 50)",
    ),
    category_id: int = Query(
        None,
        ge=1,
        description="Optional category filter",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Max number of recommendations to return",
    ),
    db: Session = Depends(get_db),
):
    """
    Fetch recommended places near the user.

    Pipeline:
      1. PostGIS fetches nearest candidates within radius (max 300).
      2. Each candidate is scored using Bayesian rating + distance + popularity.
      3. Results sorted by composite score descending.
    """
    try:
        # Set a statement-level timeout for this query (5 seconds)
        db.execute(
            __import__("sqlalchemy").text(
                f"SET LOCAL statement_timeout = '5000'"
            )
        )

        result = recommendation_service.get_recommendations(
            session=db,
            latitude=lat,
            longitude=lng,
            radius_km=radius_km,
            category_id=category_id,
            limit=limit,
            candidate_limit=300,
        )
        return result

    except APIException:
        raise
    except Exception as e:
        logger.error("Recommendation endpoint error: %s", str(e), exc_info=True)
        raise APIException(
            "Failed to fetch recommendations. Please try again.",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
