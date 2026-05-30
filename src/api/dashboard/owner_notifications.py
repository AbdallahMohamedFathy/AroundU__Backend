from fastapi import APIRouter, Depends, Query, BackgroundTasks
from typing import List
from src.core.dependencies import get_uow
from src.schemas.notification_request import NotificationRequestCreate, NotificationRequestResponse
from src.services import notification_request_service
from src.api.dashboard.dependencies import owner_guard

router = APIRouter(dependencies=[Depends(owner_guard)])

@router.post("/request", response_model=NotificationRequestResponse)
def send_notification(
    payload: NotificationRequestCreate,
    background_tasks: BackgroundTasks,
    uow = Depends(get_uow),
    current_owner = Depends(owner_guard)
):
    """
    Send a push notification directly to users.
    Rate limited to 5 per day. Targets: ALL_USERS or SPECIFIC_USER only.
    """
    return notification_request_service.send_owner_notification(
        uow, current_owner.id, payload, background_tasks, current_owner.full_name
    )

@router.get("/requests", response_model=List[NotificationRequestResponse])
def get_owner_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    uow = Depends(get_uow),
    current_owner = Depends(owner_guard)
):
    """List sent notifications for the current owner."""
    items = uow.notification_request_repository.get_by_sender_id(current_owner.id, skip, limit)

    responses = []
    for i in items:
        resp = NotificationRequestResponse.model_validate(i)
        stats = uow.notification_repository.get_request_stats(i.id)
        resp.total_sent = stats["total_sent"]
        resp.read_count = stats["read_count"]
        responses.append(resp)

    return responses
