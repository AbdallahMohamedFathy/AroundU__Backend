from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base

class NotificationType(str, Enum):
    NEW_REVIEW = "NEW_REVIEW"
    NEW_PROPERTY_REVIEW = "NEW_PROPERTY_REVIEW"
    PROPERTY_APPROVED = "PROPERTY_APPROVED"
    PROPERTY_REJECTED = "PROPERTY_REJECTED"
    SYSTEM_ALERT = "SYSTEM_ALERT"

class NotificationPriority(str, Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    data = Column(JSON, nullable=True) # For structured payload (place_id, property_id, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", backref="notifications")

    # Optimization Indexes
    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read"),
        Index("ix_notifications_created_at_desc", created_at.desc()),
    )
