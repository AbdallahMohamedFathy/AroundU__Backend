from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=True) # Source of Truth for Google Auth
    provider = Column(String, nullable=True, server_default="local") # google or local
    
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True) # Nullable because Google users might not grant email
    password_hash = Column(String, nullable=True) # Nullable for Social Auth users
    role = Column(String, nullable=False, server_default="USER")
    owner_type = Column(String, nullable=True) # Optional for migration stability
    
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Soft deletes
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    @property
    def is_admin(self):
        return self.role == "ADMIN"

    @property
    def is_owner(self):
        return self.role == "OWNER"

    verification_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    places = relationship("Place", back_populates="owner")
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    property_reviews = relationship("PropertyReview", back_populates="user", cascade="all, delete-orphan")
    property_favorites = relationship("PropertyFavorite", back_populates="user", cascade="all, delete-orphan")
    
    # New Auth Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    device_tokens = relationship("DeviceToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
