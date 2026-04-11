from fastapi import APIRouter, Depends, Query
from typing import List
from src.core.dependencies import get_uow
from src.schemas.notification_request import NotificationRequestCreate, NotificationRequestResponse
from src.services import notification_request_service
from src.api.dashboard.dependencies import owner_guard

router = APIRouter(dependencies=[Depends(owner_guard)])

@router.post("/request", response_model=NotificationRequestResponse)
def create_request(
    payload: NotificationRequestCreate,
    uow = Depends(get_uow),
    current_owner = Depends(owner_guard)
):
    """
    Request an admin approval to blast a push notification.
    Rate limited to 5 per owner per day.
    """
    return notification_request_service.create_notification_request(uow, current_owner.id, payload)

@router.get("/requests", response_model=List[NotificationRequestResponse])
def get_owner_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    uow = Depends(get_uow),
    current_owner = Depends(owner_guard)
):
    """List pending and resolved notification requests belonging to the current owner."""
    items = uow.notification_request_repository.get_by_sender_id(current_owner.id, skip, limit)
    return [NotificationRequestResponse.model_validate(i) for i in items]
