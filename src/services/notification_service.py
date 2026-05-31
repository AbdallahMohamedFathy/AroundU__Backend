import logging
from typing import List, Optional
from fastapi import BackgroundTasks
from sqlalchemy import select
from src.core.unit_of_work import UnitOfWork
from src.models.notification import Notification, NotificationType, NotificationPriority
from src.models.device import DeviceToken
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
    background_tasks: Optional[BackgroundTasks] = None,
    sender_id: Optional[int] = None,
    sender_name: Optional[str] = None,
):
    """
    Saves a notification to the database and sends a push notification via FCM.
    Failsafe: Database save persists even if FCM fails.
    """
    merged_data = dict(data or {})
    if sender_id is not None:
        merged_data["sender_id"] = sender_id
    if sender_name is not None:
        merged_data["sender_name"] = sender_name

    with uow:
        new_notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            priority=priority,
            data=merged_data,
        )
        uow.notification_repository.create(new_notif)

        # Fetch all active FCM tokens for this user from DeviceToken table
        fcm_tokens = uow.session.execute(
            select(DeviceToken.fcm_token).filter(
                DeviceToken.user_id == user_id,
                DeviceToken.is_active == True
            )
        ).scalars().all()

        uow.commit()

    # Send push notification to every active device
    if fcm_tokens:
        payload = {
            "notif_id": str(new_notif.id),
            "type": notif_type.value,
            **(data or {})
        }
        for token in fcm_tokens:
            if background_tasks:
                background_tasks.add_task(
                    send_push_notification,
                    token, title, message, payload, priority
                )
            else:
                await send_push_notification(token, title, message, payload, priority)

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
    background_tasks: Optional[BackgroundTasks] = None,
    sender_id: Optional[int] = None,
    sender_name: Optional[str] = None,
):
    """
    Optimized bulk notification creation for multiple users in chunks.
    Uses FCM multicast messaging in batches of 500.
    """
    BATCH_SIZE = 500

    merged_data = dict(data or {})
    if sender_id is not None:
        merged_data["sender_id"] = sender_id
    if sender_name is not None:
        merged_data["sender_name"] = sender_name

    with uow:
        for i in range(0, len(user_ids), BATCH_SIZE):
            chunk_ids = user_ids[i:i + BATCH_SIZE]
            notifications_data = [
                {
                    "user_id": uid,
                    "request_id": request_id,
                    "title": title,
                    "message": message,
                    "type": notif_type,
                    "priority": priority,
                    "data": merged_data,
                }
                for uid in chunk_ids
            ]
            uow.notification_repository.bulk_create(notifications_data)
        uow.commit()

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
    Fetches FCM tokens from DeviceToken table and dispatches multicast messages.
    Removes dead tokens on failure.
    """
    from src.core.database import SessionLocal
    BATCH_SIZE = 500

    try:
        app = get_firebase_app()
    except Exception as e:
        logger.error(f"FCM skipped: Firebase not initialized: {e}")
        return

    if not app:
        return

    db = SessionLocal()
    try:
        for i in range(0, len(user_ids), BATCH_SIZE):
            chunk_ids = user_ids[i:i + BATCH_SIZE]

            records = db.execute(
                select(DeviceToken.user_id, DeviceToken.fcm_token).filter(
                    DeviceToken.user_id.in_(chunk_ids),
                    DeviceToken.is_active == True
                )
            ).all()

            if not records:
                continue

            target_tokens = []
            token_to_uid_map = {}
            for row in records:
                uid, tk = row
                target_tokens.append(tk)
                token_to_uid_map[tk] = uid

            string_data = {k: str(v) for k, v in (data or {}).items()}
            string_data["type"] = notif_type.value
            android_priority = "high" if priority == NotificationPriority.HIGH else "normal"

            from firebase_admin import messaging
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

            try:
                response = messaging.send_each_for_multicast(msg)

                dead_tokens = []
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        err_code = resp.exception.code if resp.exception else None
                        if err_code in ["invalid-registration-token", "registration-token-not-registered"]:
                            dead_tokens.append(target_tokens[idx])

                if dead_tokens:
                    logger.warning(f"Removing {len(dead_tokens)} dead FCM tokens.")
                    db.query(DeviceToken).filter(
                        DeviceToken.fcm_token.in_(dead_tokens)
                    ).delete(synchronize_session=False)
                    db.commit()

            except Exception as e:
                logger.error(f"FCM Multicast error: {e}")

    finally:
        db.close()


async def send_push_notification(
    token: str, title: str, body: str,
    data: Optional[dict] = None, priority: NotificationPriority = NotificationPriority.NORMAL
):
    """Send a single push notification and clean up dead token on failure."""
    try:
        app = get_firebase_app()
    except Exception as e:
        logger.error(f"FCM skipped: Firebase not initialized: {e}")
        return False

    if not app:
        return False

    string_data = {k: str(v) for k, v in (data or {}).items()}
    android_priority = "high" if priority == NotificationPriority.HIGH else "normal"

    from firebase_admin import messaging
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
        messaging.send(msg)
        return True
    except messaging.ApiCallError as e:
        if e.code in ["invalid-registration-token", "registration-token-not-registered"]:
            _cleanup_dead_token(token)
        return False
    except Exception:
        return False


def _cleanup_dead_token(token: str):
    """Delete a single dead FCM token from DeviceToken table."""
    from src.core.database import SessionLocal
    db = SessionLocal()
    try:
        db.query(DeviceToken).filter(DeviceToken.fcm_token == token).delete()
        db.commit()
    except Exception as e:
        logger.error(f"Error cleaning up FCM token: {e}")
    finally:
        db.close()


_ORDER_STATUS_MAP = {
    "PENDING":           ("طلبك وصلنا ✅",          "استلمنا طلبك وبنراجعه"),
    "CONFIRMED":         ("تم قبول طلبك ✅",         "المطعم قبل طلبك وبيبدأ التحضير"),
    "PREPARING":         ("جاري تجهيز طلبك 👨‍🍳",     "طلبك بيتجهز دلوقتي"),
    "READY_FOR_PICKUP":  ("طلبك جاهز 🎉",           "الطلب جاهز للاستلام"),
    "OUT_FOR_DELIVERY":  ("الدليفري في الطريق 🛵",    "طلبك جاي هيوصل قريبًا"),
    "COMPLETED":         ("تم توصيل طلبك 🎉",        "وصل طلبك! استمتع بوجبتك"),
    "CANCELLED":         ("تم إلغاء طلبك",           "تم إلغاء الطلب. في أي مشكلة تواصل معنا"),
}


async def send_order_status_notification(
    db,
    user_id: int,
    order_id: int,
    status: str,
    place_name: str = "",
):
    """
    Saves an order status notification to DB and sends FCM push.
    Uses the exact payload format expected by the Flutter app:
    - channel_id: 7waleek_orders
    - android.priority: high / notification.priority: max
    - APNS badge: 1, sound: default
    """
    from sqlalchemy import select as sa_select
    from src.models.notification import Notification, NotificationType, NotificationPriority
    from src.models.device import DeviceToken

    title, body = _ORDER_STATUS_MAP.get(status, ("تحديث في طلبك", ""))
    full_body = f"{place_name} — {body}" if place_name else body

    notif_data = {
        "type": "order_status",
        "order_id": str(order_id),
        "status": status,
        "place_name": place_name or "",
        "route": "orders",
    }

    # Save to notifications table (non-blocking on failure)
    try:
        new_notif = Notification(
            user_id=user_id,
            title=title,
            message=full_body,
            type=NotificationType.ORDER_STATUS,
            priority=NotificationPriority.HIGH,
            data=notif_data,
        )
        db.add(new_notif)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to save order notification to DB: {e}")
        try:
            await db.rollback()
        except Exception:
            pass

    # Fetch active FCM tokens for the user
    try:
        tokens_result = await db.execute(
            sa_select(DeviceToken.fcm_token).where(
                DeviceToken.user_id == user_id,
                DeviceToken.is_active == True,
            )
        )
        fcm_tokens = tokens_result.scalars().all()
    except Exception as e:
        logger.error(f"Failed to fetch FCM tokens for order notification: {e}")
        return

    for token in fcm_tokens:
        await _send_order_fcm(token, title, full_body, notif_data)


async def _send_order_fcm(token: str, title: str, body: str, data: dict):
    """Send a single FCM message with order-specific channel and max priority."""
    try:
        app = get_firebase_app()
    except Exception as e:
        logger.error(f"FCM skipped: Firebase not initialized: {e}")
        return

    if not app:
        return

    string_data = {k: str(v) for k, v in data.items()}

    from firebase_admin import messaging
    msg = messaging.Message(
        token=token,
        notification=messaging.Notification(title=title, body=body),
        data=string_data,
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                channel_id="7waleek_orders",
                sound="default",
                priority="max",
            ),
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound="default", badge=1)
            ),
            headers={"apns-priority": "10"},
        ),
    )

    try:
        messaging.send(msg)
    except Exception as e:
        logger.error(f"FCM order notification send failed: {e}")
        err_code = getattr(e, "code", None)
        if err_code in ["invalid-registration-token", "registration-token-not-registered"]:
            _cleanup_dead_token(token)


def mark_notification_as_read(uow: UnitOfWork, notification_id: int, user_id: int):
    """Marks a specific notification as read after validating ownership."""
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
