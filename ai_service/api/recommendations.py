from fastapi import APIRouter, HTTPException
from ai_service.services.recommendation_service import recommendation_service

router = APIRouter()

@router.get("/{user_id}")
async def get_recommendations(user_id: int):
    try:
        recommendations = await recommendation_service.get_recommendations(user_id)
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
