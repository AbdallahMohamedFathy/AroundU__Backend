from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from src.core.database import Base


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    fcm_token = Column(String, unique=True, nullable=False, index=True)
    device_model = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    last_active_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="device_tokens")
    refresh_tokens = relationship("RefreshToken", back_populates="device", cascade="all, delete-orphan")
