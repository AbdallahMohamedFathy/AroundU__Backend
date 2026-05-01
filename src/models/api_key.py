from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func
from src.core.database import Base

class ServiceAPIKey(Base):
    __tablename__ = "service_api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String, nullable=False)
    api_key_hash = Column(String, unique=True, index=True, nullable=False)
    permissions = Column(JSON, nullable=False) # e.g. ["read:places", "read:interactions"]
    allowed_ips = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
