from sqlalchemy.orm import Session
from src.core.repository import BaseRepository
from src.models.notification_audit import NotificationAudit

class NotificationAuditRepository(BaseRepository[NotificationAudit]):
    def __init__(self, session: Session):
        super().__init__(NotificationAudit, session)
