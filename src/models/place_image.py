from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base


class PlaceImage(Base):
    __tablename__ = "place_images"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(String, nullable=False)
    image_type = Column(String(20), nullable=False) # 'place' or 'menu'
    caption = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    place = relationship("Place", back_populates="images")
