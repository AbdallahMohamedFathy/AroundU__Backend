from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from typing import List, Optional
import math

from src.core.unit_of_work import UnitOfWork
from src.core.dependencies import get_current_user, get_uow
from src.schemas.notification import (
    NotificationResponse, 
    PaginatedNotificationResponse, 
    FCMTokenUpdate
)
from src.services.notification_service import mark_notification_as_read
from src.models.user import User

router = APIRouter()

@router.post("/fcm-token", status_code=status.HTTP_200_OK)
async def update_fcm_token(
    data: FCMTokenUpdate,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Update or save the current user's FCM token for push notifications.
    """
    with uow:
        user = uow.user_repository.get_by_id(current_user.id)
        user.fcm_token = data.fcm_token
        uow.commit()
    
    return {"status": "success", "message": "FCM token updated successfully"}


@router.get("/", response_model=PaginatedNotificationResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Get a paginated list of notifications for the authenticated user.
    Ordered by latest first.
    """
    with uow:
        items, total = uow.notification_repository.get_user_notifications(
            user_id=current_user.id,
            page=page,
            limit=limit
        )
        
        # Convert model instances to schemas
        # We do this inside the unit of work to avoid DetachedInstanceError
        # although with simple fields it might not be necessary.
        responses = [NotificationResponse.model_validate(item) for item in items]
        
        total_pages = math.ceil(total / limit) if total > 0 else 0
        
        return {
            "items": responses,
            "total": total,
            "page": page,
            "page_size": limit,
            "total_pages": total_pages
        }


@router.patch("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Mark a specific notification as read.
    """
    mark_notification_as_read(uow, notification_id, current_user.id)
    return {"status": "success", "message": "Notification marked as read"}


@router.post("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Mark all notifications for the current user as read.
    """
    with uow:
        uow.notification_repository.mark_all_as_read(current_user.id)
        uow.commit()
    return {"status": "success", "message": "All notifications marked as read"}


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Get the count of unread notifications for the current user.
    """
    with uow:
        count = uow.notification_repository.get_unread_count(current_user.id)
    return {"unread_count": count}
