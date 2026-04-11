from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.core.repository import BaseRepository
from src.models.notification_request import NotificationRequest, RequestStatus
from datetime import datetime, timezone

class NotificationRequestRepository(BaseRepository[NotificationRequest]):
    def __init__(self, session: Session):
        super().__init__(NotificationRequest, session)

    def count_daily_by_sender(self, sender_id: int) -> int:
        """Count requests sent by user today."""
        today = datetime.now(timezone.utc).date()
        return self.session.query(func.count(NotificationRequest.id)).filter(
            NotificationRequest.sender_id == sender_id,
            func.date(NotificationRequest.created_at) == today
        ).scalar() or 0

    def get_by_sender_id(self, sender_id: int, skip: int = 0, limit: int = 20) -> List[NotificationRequest]:
        return self.session.query(NotificationRequest).filter(
            NotificationRequest.sender_id == sender_id,
            NotificationRequest.is_archived == False
        ).order_by(NotificationRequest.created_at.desc()).offset(skip).limit(limit).all()

    def get_all_paginated(
        self, skip: int = 0, limit: int = 20, status: Optional[RequestStatus] = None
    ) -> Tuple[List[NotificationRequest], int]:
        query = self.session.query(NotificationRequest).filter(NotificationRequest.is_archived == False)
        if status:
            query = query.filter(NotificationRequest.status == status)
        
        total = query.count()
        items = query.order_by(NotificationRequest.created_at.desc()).offset(skip).limit(limit).all()
        return items, total
