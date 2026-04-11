from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from src.models.notification_request import TargetType, RequestStatus

class NotificationRequestBase(BaseModel):
    title: str
    message: str
    target_type: TargetType
    target_user_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None

class NotificationRequestCreate(NotificationRequestBase):
    """Payload an owner sends to request a notification."""
    pass

class AdminNotificationSend(NotificationRequestBase):
    """Payload an admin sends for direct notification blast."""
    pass

class NotificationRequestResponse(NotificationRequestBase):
    """Data returned to clients."""
    id: int
    sender_id: int
    sender_name: Optional[str] = None
    status: RequestStatus
    is_archived: bool
    created_at: datetime
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    total_sent: Optional[int] = 0
    read_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
