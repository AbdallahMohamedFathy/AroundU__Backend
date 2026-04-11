from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any, List
from src.models.notification import NotificationType, NotificationPriority

class NotificationBase(BaseModel):
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Optional[dict] = None

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationUpdate(BaseModel):
    is_read: bool

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedNotificationResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class FCMTokenUpdate(BaseModel):
    fcm_token: str
