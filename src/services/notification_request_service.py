from typing import List, Optional
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import select
from src.core.unit_of_work import UnitOfWork
from src.models.user import User
from src.models.notification import NotificationType, NotificationPriority
from src.models.notification_request import NotificationRequest, TargetType, RequestStatus
from src.models.notification_audit import NotificationAudit, AuditAction
from src.schemas.notification_request import NotificationRequestCreate, AdminNotificationSend
from src.services.notification_service import create_bulk_notifications

MAX_DAILY_OWNER_REQUESTS = 5

def create_notification_request(
    uow: UnitOfWork,
    sender_id: int,
    request_data: NotificationRequestCreate
) -> NotificationRequest:
    """Create a new request ensuring the owner has not exceeded the daily rate limit."""
    # Security: Owners can only target ALL_USERS or SPECIFIC_USER
    user = uow.user_repository.get_by_id(sender_id)
    if user and user.role == "OWNER":
        if request_data.target_type not in [TargetType.ALL_USERS, TargetType.SPECIFIC_USER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owners are restricted to targeting consumers only."
            )

    daily_count = uow.notification_request_repository.count_daily_by_sender(sender_id)
    if daily_count >= MAX_DAILY_OWNER_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit of {MAX_DAILY_OWNER_REQUESTS} notification requests exceeded."
        )

    # Validate target user if SPECIFIC_USER
    if request_data.target_type == TargetType.SPECIFIC_USER:
        if not request_data.target_user_id:
            raise HTTPException(status_code=400, detail="target_user_id is required for SPECIFIC_USER")

        target_user = uow.user_repository.get_by_id(request_data.target_user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail=f"Target user with ID {request_data.target_user_id} not found")

    new_req = NotificationRequest(
        sender_id=sender_id,
        title=request_data.title,
        message=request_data.message,
        target_type=request_data.target_type,
        target_user_id=request_data.target_user_id,
        data=request_data.data
    )
    uow.notification_request_repository.create(new_req)
    uow.commit()
    uow.session.refresh(new_req)
    return new_req

def approve_request(
    uow: UnitOfWork,
    request_id: int,
    admin_id: int,
    background_tasks: BackgroundTasks
) -> NotificationRequest:
    """Idempotent approval that resolves targets and triggers background bulk push."""
    from datetime import datetime, timezone

    with uow:
        req = uow.notification_request_repository.get_by_id_with_details(request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Idempotency
        if req.status != RequestStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Request is already {req.status.value}")

        req.status = RequestStatus.APPROVED
        req.approved_by = admin_id
        req.approved_at = datetime.now(timezone.utc)

        audit = NotificationAudit(request_id=req.id, admin_id=admin_id, action=AuditAction.APPROVED)
        uow.notification_audit_repository.create(audit)

        target_ids = resolve_targets(uow, req.target_type, req.target_user_id)
        
        uow.commit()

    if target_ids:
        # Enqueue push out of transaction
        background_tasks.add_task(
            _trigger_bulk_system_alert,
            user_ids=target_ids,
            title=req.title,
            message=req.message,
            data=req.data,
            request_id=req.id,
            sender_id=req.sender_id,
            sender_name=req.sender_name,
        )

    return req

def reject_request(
    uow: UnitOfWork,
    request_id: int,
    admin_id: int
) -> NotificationRequest:
    """Idempotent rejection logging."""
    from datetime import datetime, timezone

    with uow:
        req = uow.notification_request_repository.get_by_id_with_details(request_id)
        if not req: raise HTTPException(status_code=404, detail="Request not found")
        if req.status != RequestStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Request is already {req.status.value}")

        req.status = RequestStatus.REJECTED
        req.approved_by = admin_id
        req.approved_at = datetime.now(timezone.utc)

        audit = NotificationAudit(request_id=req.id, admin_id=admin_id, action=AuditAction.REJECTED)
        uow.notification_audit_repository.create(audit)
        
        uow.commit()
    return req

def archive_request(uow: UnitOfWork, request_id: int) -> bool:
    """Soft delete/Archive."""
    with uow:
        req = uow.notification_request_repository.get_by_id(request_id)
        if not req: raise HTTPException(status_code=404, detail="Request not found")
        req.is_archived = True
        uow.commit()
    return True

def resolve_targets(uow: UnitOfWork, target_type: TargetType, specific_id: Optional[int]) -> List[int]:
    """Memory-optimized lookup returning flat lists of user IDs."""
    if target_type == TargetType.ALL_USERS:
        rows = uow.session.execute(select(User.id).filter(User.is_active == True)).all()
        return [r[0] for r in rows]
    elif target_type == TargetType.ALL_OWNERS:
        rows = uow.session.execute(select(User.id).filter(User.role == "OWNER", User.is_active == True)).all()
        return [r[0] for r in rows]
    elif target_type == TargetType.SPECIFIC_OWNER:
        if not specific_id: return []
        row = uow.session.execute(select(User.id).filter(User.id == specific_id, User.role == "OWNER")).first()
        return [row[0]] if row else []
    elif target_type == TargetType.SPECIFIC_USER:
        if not specific_id: return []
        row = uow.session.execute(select(User.id).filter(User.id == specific_id)).first()
        return [row[0]] if row else []
    return []

async def _trigger_bulk_system_alert(
    user_ids: List[int],
    title: str,
    message: str,
    data: Optional[dict],
    request_id: Optional[int] = None,
    sender_id: Optional[int] = None,
    sender_name: Optional[str] = None,
):
    """Helper used to jumpstart background async from sync approve context."""
    from src.core.database import SessionLocal
    uow = UnitOfWork(SessionLocal)
    # Pass background_tasks=None so create_bulk_notifications awaits FCM directly
    # (we are already running in a background task — a fake BackgroundTasks() would
    #  silently swallow the FCM call and never execute it)
    await create_bulk_notifications(
        uow=uow,
        user_ids=user_ids,
        title=title,
        message=message,
        notif_type=NotificationType.SYSTEM_ALERT,
        data=data,
        priority=NotificationPriority.HIGH,
        request_id=request_id,
        sender_id=sender_id,
        sender_name=sender_name,
        background_tasks=None,
    )


def send_admin_notification(
    uow: UnitOfWork,
    payload: AdminNotificationSend,
    background_tasks: BackgroundTasks,
    sender_name: str = "7waleek",
):
    """Direct blast bypassing Request-Approval flow."""
    target_ids = resolve_targets(uow, payload.target_type, payload.target_user_id)
    if target_ids:
        background_tasks.add_task(
            _trigger_bulk_system_alert,
            user_ids=target_ids,
            title=payload.title,
            message=payload.message,
            data=payload.data,
            sender_name=sender_name,
        )
    return {"status": "success", "targeted_users": len(target_ids)}


def send_owner_notification(
    uow: UnitOfWork,
    sender_id: int,
    request_data: NotificationRequestCreate,
    background_tasks: BackgroundTasks,
    sender_name: str,
) -> NotificationRequest:
    """Owner sends notification directly without admin approval. Rate limited to 5/day."""
    from datetime import datetime, timezone

    if request_data.target_type not in [TargetType.ALL_USERS, TargetType.SPECIFIC_USER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owners are restricted to targeting consumers only."
        )

    daily_count = uow.notification_request_repository.count_daily_by_sender(sender_id)
    if daily_count >= MAX_DAILY_OWNER_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit of {MAX_DAILY_OWNER_REQUESTS} notification requests exceeded."
        )

    if request_data.target_type == TargetType.SPECIFIC_USER:
        if not request_data.target_user_id:
            raise HTTPException(status_code=400, detail="target_user_id is required for SPECIFIC_USER")
        if not uow.user_repository.get_by_id(request_data.target_user_id):
            raise HTTPException(status_code=404, detail=f"Target user {request_data.target_user_id} not found")

    new_req = NotificationRequest(
        sender_id=sender_id,
        title=request_data.title,
        message=request_data.message,
        target_type=request_data.target_type,
        target_user_id=request_data.target_user_id,
        data=request_data.data,
        status=RequestStatus.APPROVED,
        approved_at=datetime.now(timezone.utc),
    )
    uow.notification_request_repository.create(new_req)
    uow.commit()
    uow.session.refresh(new_req)

    target_ids = resolve_targets(uow, request_data.target_type, request_data.target_user_id)

    if target_ids:
        background_tasks.add_task(
            _trigger_bulk_system_alert,
            user_ids=target_ids,
            title=request_data.title,
            message=request_data.message,
            data=request_data.data,
            request_id=new_req.id,
            sender_id=sender_id,
            sender_name=sender_name,
        )

    return new_req
