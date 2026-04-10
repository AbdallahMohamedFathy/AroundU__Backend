from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from src.core.database import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    main_image_url = Column(String, nullable=True)
    contact_number = Column(String, nullable=True)
    whatsapp_number = Column(String, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    @property
    def review_count(self) -> int:
        return len(getattr(self, "reviews", []))

    # Relationships
    owner = relationship("User", backref="properties")
    images = relationship("PropertyImage", back_populates="prop", cascade="all, delete-orphan")
    reviews = relationship("PropertyReview", back_populates="prop", cascade="all, delete-orphan")
