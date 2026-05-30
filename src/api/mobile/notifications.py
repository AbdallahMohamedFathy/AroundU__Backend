from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    from src.models.device import DeviceToken
    from datetime import datetime, timezone

    existing = uow.session.query(DeviceToken).filter(
        DeviceToken.fcm_token == data.fcm_token
    ).first()

    if existing:
        existing.user_id = current_user.id
        existing.is_active = True
        existing.last_active_at = datetime.now(timezone.utc)
    else:
        uow.session.add(DeviceToken(
            user_id=current_user.id,
            fcm_token=data.fcm_token,
        ))

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


@router.delete("/clear-all", status_code=status.HTTP_200_OK)
async def clear_all_notifications(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Delete all notifications for the current user.
    """
    with uow:
        uow.notification_repository.delete_all_for_user(current_user.id)
        uow.commit()
        
    return {"status": "success", "message": "All notifications deleted successfully"}


@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow)
):
    """
    Delete a specific notification.
    """
    with uow:
        notification = uow.notification_repository.get_by_id(notification_id)
        if not notification or notification.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        uow.notification_repository.delete(notification)
        uow.commit()
        
    return {"status": "success", "message": "Notification deleted successfully"}
