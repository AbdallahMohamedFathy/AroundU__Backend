import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from src.core.database import Base

class AuditAction(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class NotificationAudit(Base):
    __tablename__ = "notification_audits"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("notification_requests.id", ondelete="CASCADE"), nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(Enum(AuditAction, name="notification_audit_action"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    request = relationship("NotificationRequest")
    admin = relationship("User", foreign_keys=[admin_id])
