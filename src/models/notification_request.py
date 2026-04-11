import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from src.core.database import Base

class TargetType(str, enum.Enum):
    ALL_USERS = "ALL_USERS"
    ALL_OWNERS = "ALL_OWNERS"
    SPECIFIC_OWNER = "SPECIFIC_OWNER"
    SPECIFIC_USER = "SPECIFIC_USER"

class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class NotificationRequest(Base):
    __tablename__ = "notification_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(Enum(TargetType, name="notification_target_type"), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    status = Column(Enum(RequestStatus, name="notification_request_status"), default=RequestStatus.PENDING, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    sender = relationship("User", foreign_keys=[sender_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    approver = relationship("User", foreign_keys=[approved_by])
