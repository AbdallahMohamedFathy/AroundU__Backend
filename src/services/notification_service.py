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
    request_id: Optional[int] = None,
    background_tasks: Optional[BackgroundTasks] = None
):
    """
    Optimized bulk notification creation for multiple users in chunks.
    NEVER loads full User objects into memory.
    Uses FCM multicast messaging array in batches of 500.
    """
    BATCH_SIZE = 500
    
    with uow:
        # DB limits: bulk insert in chunks to avoid memory errors
        for i in range(0, len(user_ids), BATCH_SIZE):
            chunk_ids = user_ids[i:i + BATCH_SIZE]
            notifications_data = [
                {
                    "user_id": uid,
                    "request_id": request_id, # Link to the blast request
                    "title": title,
                    "message": message,
                    "type": notif_type,
                    "priority": priority,
                    "data": data or {}
                }
                for uid in chunk_ids
            ]
            uow.notification_repository.bulk_create(notifications_data)
        uow.commit()

    # Deferred push logic out of the DB transaction lock
    if background_tasks:
        background_tasks.add_task(
            _process_multicast_batches,
            user_ids, title, message, notif_type, data, priority
        )
    return True


async def _process_multicast_batches(
    user_ids: List[int], title: str, message: str, 
    notif_type: NotificationType, data: Optional[dict], priority: NotificationPriority
):
    """
    Fetches tokens efficiently and dispatches FCM Multicast messaging securely.
    Identifies invalid tokens and removes them from the DB in bulk.
    """
    from src.core.database import SessionLocal
    from sqlalchemy import select
    BATCH_SIZE = 500

    try:
        app = get_firebase_app()
    except Exception as e:
        logger.error(f"FCM skipped: Firebase not initialized: {e}")
        return

    if not app:
        return

    # Efficient fetch without loading models
    db = SessionLocal()
    try:
        # Process in chunks of 500
        for i in range(0, len(user_ids), BATCH_SIZE):
            chunk_ids = user_ids[i:i + BATCH_SIZE]
            
            # Fetch token map {fcm_token: user_id}
            records = db.execute(
                select(User.id, User.fcm_token)
                .filter(User.id.in_(chunk_ids), User.fcm_token.isnot(None))
            ).all()

            if not records:
                continue

            target_tokens = []
            token_to_uid_map = {}
            for row in records:
                uid, tk = row
                target_tokens.append(tk)
                token_to_uid_map[tk] = uid

            # Payload
            string_data = {k: str(v) for k, v in (data or {}).items()}
            string_data["type"] = notif_type.value
            android_priority = "high" if priority == NotificationPriority.HIGH else "normal"

            msg = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=message),
                data=string_data,
                tokens=target_tokens,
                android=messaging.AndroidConfig(priority=android_priority),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(content_available=True) if priority == NotificationPriority.HIGH else messaging.Aps()
                    )
                )
            )

            # Multicast Send
            try:
                response = messaging.send_each_for_multicast(msg)
                
                # Check for dead tokens
                invalid_uids = []
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        err_code = resp.exception.code if resp.exception else None
                        if err_code in ["invalid-registration-token", "registration-token-not-registered"]:
                            dead_token = target_tokens[idx]
                            invalid_uids.append(token_to_uid_map[dead_token])
                
                # Bulk remove dead tokens
                if invalid_uids:
                    logger.warning(f"Removing {len(invalid_uids)} dead FCM tokens.")
                    db.query(User).filter(User.id.in_(invalid_uids)).update({"fcm_token": None}, synchronize_session=False)
                    db.commit()

            except Exception as e:
                logger.error(f"FCM Multicast error: {e}")

    finally:
        db.close()


async def send_push_notification(
    user_id: int, token: str, title: str, body: str, 
    data: Optional[dict] = None, priority: NotificationPriority = NotificationPriority.NORMAL
):
    """
    Fallback method for sending a single push notification.
    """
    try:
        app = get_firebase_app()
    except Exception as e:
        logger.error(f"FCM skipped: Firebase not initialized: {e}")
        return False
        
    if not app: return False
    
    string_data = {k: str(v) for k, v in (data or {}).items()}
    android_priority = "high" if priority == NotificationPriority.HIGH else "normal"
    
    msg = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=string_data,
        token=token,
        android=messaging.AndroidConfig(priority=android_priority),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(content_available=True) if priority == NotificationPriority.HIGH else messaging.Aps()
            )
        )
    )

    try:
        response = messaging.send(msg)
        return True
    except messaging.ApiCallError as e:
        if e.code in ["invalid-registration-token", "registration-token-not-registered"]:
            _cleanup_user_token(user_id)
        return False
    except Exception:
        return False


def _cleanup_user_token(user_id: int):
    """Fallback single cleanup"""
    from src.core.database import SessionLocal
    db = SessionLocal()
    try:
        db.query(User).filter(User.id == user_id).update({"fcm_token": None})
        db.commit()
    except Exception as e:
        logger.error(f"Error cleaning up token: {e}")
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
