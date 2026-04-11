from fastapi import APIRouter, Depends, Query, BackgroundTasks
from typing import List, Optional
from src.core.dependencies import get_uow
from src.schemas.notification_request import NotificationRequestResponse, AdminNotificationSend
from src.models.notification_request import RequestStatus
from src.services import notification_request_service
from src.api.dashboard.dependencies import admin_guard

router = APIRouter(dependencies=[Depends(admin_guard)])

@router.get("/requests", response_model=dict)
def get_all_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[RequestStatus] = Query(None),
    uow = Depends(get_uow),
    current_admin = Depends(admin_guard)
):
    """Paginated list of notification requests with status filtering."""
    items, total = uow.notification_request_repository.get_all_paginated(skip, limit, status)
    
    # Map items to include sender_name from the sender relationship
    enhanced_items = []
    for i in items:
        resp = NotificationRequestResponse.model_validate(i)
        if i.sender:
            resp.sender_name = i.sender.full_name
        enhanced_items.append(resp)
        
    return {
        "items": enhanced_items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.post("/requests/{request_id}/approve", response_model=NotificationRequestResponse)
def approve_request(
    request_id: int,
    background_tasks: BackgroundTasks,
    uow = Depends(get_uow),
    current_admin = Depends(admin_guard)
):
    """Approve a PENDING request and dispatch FCM blast."""
    return notification_request_service.approve_request(uow, request_id, current_admin.id, background_tasks)

@router.post("/requests/{request_id}/reject", response_model=NotificationRequestResponse)
def reject_request(
    request_id: int,
    uow = Depends(get_uow),
    current_admin = Depends(admin_guard)
):
    """Reject a PENDING request."""
    return notification_request_service.reject_request(uow, request_id, current_admin.id)

@router.post("/requests/{request_id}/archive")
def archive_request(
    request_id: int,
    uow = Depends(get_uow),
    current_admin = Depends(admin_guard)
):
    """Archive an old request."""
    notification_request_service.archive_request(uow, request_id)
    return {"message": "success"}

@router.post("/send")
def send_admin_notification(
    payload: AdminNotificationSend,
    background_tasks: BackgroundTasks,
    uow = Depends(get_uow),
    current_admin = Depends(admin_guard)
):
    """Directly blast notifications without approval flow."""
    return notification_request_service.send_admin_notification(uow, payload, background_tasks)
