from pydantic import BaseModel, Field, model_validator
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
    sender_name: Optional[str] = None
    sender_id: Optional[int] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def _extract_sender_from_data(self):
        if self.data:
            if self.sender_name is None:
                self.sender_name = self.data.get("sender_name")
            if self.sender_id is None:
                raw = self.data.get("sender_id")
                self.sender_id = int(raw) if raw is not None else None
        return self

class PaginatedNotificationResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class FCMTokenUpdate(BaseModel):
    fcm_token: str
