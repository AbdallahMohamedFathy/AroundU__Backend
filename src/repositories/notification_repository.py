from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from src.models.notification import Notification, NotificationType
from src.repositories.base_repository import BaseRepository

class NotificationRepository(BaseRepository[Notification]):
    """Repository for Notification model."""
    
    def __init__(self, session: Session):
        super().__init__(Notification, session)

    def get_user_notifications(
        self, 
        user_id: int, 
        page: int = 1, 
        limit: int = 20,
        notif_type: Optional[NotificationType] = None
    ) -> Tuple[List[Notification], int]:
        """
        Get paginated notifications for a user, ordered by creation date (desc).
        """
        query = self.session.query(Notification).filter(Notification.user_id == user_id)
        
        if notif_type:
            query = query.filter(Notification.type == notif_type)
            
        total = query.count()
        
        items = query.order_by(desc(Notification.created_at)) \
                     .offset((page - 1) * limit) \
                     .limit(limit) \
                     .all()
                     
        return items, total

    def bulk_create(self, notifications_data: List[dict]):
        """
        Efficiently create multiple notifications at once.
        """
        if not notifications_data:
            return
            
        self.session.bulk_insert_mappings(Notification, notifications_data)

    def mark_all_as_read(self, user_id: int):
        """
        Mark all notifications for a user as read.
        """
        self.session.query(Notification) \
            .filter(Notification.user_id == user_id, Notification.is_read == False) \
            .update({"is_read": True}, synchronize_session=False)

    def get_unread_count(self, user_id: int) -> int:
        """
        Get the count of unread notifications for a user.
        """
        return self.session.query(Notification) \
            .filter(Notification.user_id == user_id, Notification.is_read == False) \
            .count()

    def get_all_paginated(
        self, 
        skip: int = 0, 
        limit: int = 20,
        notif_type: Optional[NotificationType] = None,
        user_id: Optional[int] = None
    ) -> Tuple[List[Notification], int]:
        """
        Global paginated retrieval for admin auditing.
        """
        query = self.session.query(Notification)
        
        if notif_type:
            query = query.filter(Notification.type == notif_type)
        if user_id:
            query = query.filter(Notification.user_id == user_id)
            
        total = query.count()
        
        items = query.order_by(desc(Notification.created_at)) \
                     .offset(skip) \
                     .limit(limit) \
                     .all()
                     
        return items, total
