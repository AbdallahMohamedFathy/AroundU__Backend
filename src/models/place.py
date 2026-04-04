from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String, nullable=True)
    phone = Column(ARRAY(String), nullable=True)
    website = Column(String, nullable=True)
    instagram_url = Column(String, nullable=True)
    facebook_url = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    tiktok_url = Column(String, nullable=True)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0, nullable=False, server_default='0')
    search_vector = Column(TSVECTOR)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    from geoalchemy2 import Geography
    location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    parent_id = Column(
        Integer, 
        ForeignKey("places.id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Add constraints for latitude and longitude
    __table_args__ = (
        CheckConstraint('latitude >= -90 AND latitude <= 90', name='check_latitude_range'),
        CheckConstraint('longitude >= -180 AND longitude <= 180', name='check_longitude_range'),
        CheckConstraint('rating >= 0 AND rating <= 5', name='check_rating_range'),
    )

    # Relationships
    category = relationship("Category", back_populates="places")
    owner = relationship("User", back_populates="places")
    images = relationship("PlaceImage", back_populates="place", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="place", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="place", cascade="all, delete-orphan")
    items = relationship('Item', back_populates='place', cascade='all, delete-orphan')
    
    # Branch relationship (Self-referential)
    from sqlalchemy.orm import backref
    branches = relationship("Place", backref=backref("parent", remote_side=[id]), cascade="all, delete-orphan")
