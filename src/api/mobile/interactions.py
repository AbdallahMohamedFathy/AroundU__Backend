from fastapi import APIRouter, Depends, status
from src.core.dependencies import get_uow, get_current_user
from src.schemas.interaction import InteractionCreate, InteractionResponse
from src.services.ai_service import ai_connector
from src.models.interaction import Interaction
from src.models.user import User

router = APIRouter()

@router.post("/{place_id}/interactions", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
async def record_interaction(
    place_id: int,
    interaction_in: InteractionCreate,
    uow=Depends(get_uow),
    current_user: User = Depends(get_current_user)
):
    """
    Record a user interaction with a place.
    If it's a 'visit', predict the cluster using AI.
    """
    cluster_id = None
    if interaction_in.type == "visit" and interaction_in.user_lat and interaction_in.user_lon:
        cluster_data = await ai_connector.predict_cluster(interaction_in.user_lat, interaction_in.user_lon)
        if cluster_data:
            cluster_id = cluster_data.get("cluster")

    with uow:
        interaction = Interaction(
            place_id=place_id,
            user_id=current_user.id,
            type=interaction_in.type,
            user_lat=interaction_in.user_lat,
            user_lon=interaction_in.user_lon,
            cluster_id=cluster_id
        )
        uow.interaction_repository.add(interaction)
        uow.commit()
        return interaction
