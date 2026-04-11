import logging
from typing import List, Optional, Any
from fastapi import BackgroundTasks
from firebase_admin import messaging
from src.core.unit_of_work import UnitOfWork
from src.models.notification import Notification, NotificationType, NotificationPriority
from src.models.user import User
from src.utils.firebase import get_firebase_app

logger = logging.getLogger(__name__)

async def create_notification(
    uow: UnitOfWork,
    user_id: int,
    title: str,
    message: str,
    notif_type: NotificationType,
    data: Optional[dict] = None,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    background_tasks: Optional[BackgroundTasks] = None
):
    """
    Saves a notification to the database and sends a push notification via FCM.
    Failsafe: Database save persists even if FCM fails.
    """
    with uow:
        # 1. Create DB record
        new_notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            priority=priority,
            data=data or {}
        )
        uow.notification_repository.create(new_notif)
        
        # 2. Get user's FCM token
        user = uow.user_repository.get_by_id(user_id)
        fcm_token = user.fcm_token if user else None
        
        uow.commit()

    # 3. Send Push Notification (if token exists)
    if fcm_token:
        payload = {
            "notif_id": str(new_notif.id),
            "type": notif_type.value,
            **(data or {})
        }
        
        if background_tasks:
            background_tasks.add_task(
                send_push_notification, 
                user_id, 
                fcm_token, 
                title, 
                message, 
                payload, 
                priority
            )
        else:
            # Fallback for non-request contexts or if worker is preferred
            await send_push_notification(user_id, fcm_token, title, message, payload, priority)

    return new_notif


async def create_bulk_notifications(
    uow: UnitOfWork,
    user_ids: List[int],
    title: str,
    message: str,
    notif_type: NotificationType,
    data: Optional[dict] = None,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    background_tasks: Optional[BackgroundTasks] = None
):
    """
    Optimized bulk notification creation for multiple users.
    """
    with uow:
        # 1. Prepare bulk mappings for DB
        notifications_data = [
            {
                "user_id": uid,
                "title": title,
                "message": message,
                "type": notif_type,
                "priority": priority,
                "data": data or {}
            }
            for uid in user_ids
        ]
        
        # 2. Bulk insert into DB
        uow.notification_repository.bulk_create(notifications_data)
        
        # 3. Fetch user tokens for push
        users = uow.session.query(User).filter(User.id.in_(user_ids)).all()
        token_map = {user.id: user.fcm_token for user in users if user.fcm_token}
        
        uow.commit()

    # 4. Send pushes in background
    if token_map and background_tasks:
        for uid, token in token_map.items():
            payload = {"type": notif_type.value, **(data or {})}
            background_tasks.add_task(
                send_push_notification, 
                uid, 
                token, 
                title, 
                message, 
                payload, 
                priority
            )
    
    return True


async def send_push_notification(
    user_id: int,
    token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
    priority: NotificationPriority = NotificationPriority.NORMAL
):
    """
    Core logic to send a single push notification via Firebase Admin SDK.
    Includes error handling and token cleanup.
    """
    try:
        app = get_firebase_app()
    except Exception as e:
        logger.error(f"FCM skipped: Firebase not initialized: {e}")
        return False

    if not app:
        return False

    # Convert native dict to strings for FCM data payload
    string_data = {k: str(v) for k, v in (data or {}).items()}

    # Configure Priority
    android_priority = "high" if priority == NotificationPriority.HIGH else "normal"
    
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=string_data,
        token=token,
        android=messaging.AndroidConfig(
            priority=android_priority,
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(content_available=True) if priority == NotificationPriority.HIGH else messaging.Aps()
            )
        )
    )

    try:
        response = messaging.send(message)
        logger.info(f"Successfully sent push notification to user {user_id}: {response}")
        return True
    except messaging.ApiCallError as e:
        # Handle specific token errors (Invalid/Unregistered)
        # Error codes docs: https://firebase.google.com/docs/cloud-messaging/send-message#admin_sdk_error_reference
        if e.code in ["invalid-registration-token", "registration-token-not-registered"]:
            logger.warning(f"Detected inactive token for user {user_id}. Nullifying token. Error: {e.code}")
            _cleanup_user_token(user_id)
        else:
            logger.error(f"FCM API Error for user {user_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send push notification to user {user_id}: {str(e)}")
        return False


def _cleanup_user_token(user_id: int):
    """
    Helper to remove an invalid FCM token from a user.
    Called on Firebase error. Uses a fresh connection/session.
    """
    from src.core.database import SessionLocal
    db = SessionLocal()
    try:
        db.query(User).filter(User.id == user_id).update({"fcm_token": None})
        db.commit()
    except Exception as e:
        logger.error(f"Error cleaning up token for user {user_id}: {e}")
    finally:
        db.close()


def mark_notification_as_read(uow: UnitOfWork, notification_id: int, user_id: int):
    """
    Marks a specific notification as read after validating ownership.
    """
    with uow:
        notif = uow.notification_repository.get_by_id(notification_id)
        if not notif:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Notification not found")
            
        if notif.user_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Not authorized to access this notification")
            
        notif.is_read = True
        uow.commit()
        return True
