from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base

class PropertyReview(Base):
    __tablename__ = "property_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Add constraint for rating
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_property_review_rating_range'),
    )

    # Relationships
    user = relationship("User", back_populates="property_reviews")
    property = relationship("Property", back_populates="reviews")

    @property
    def user_name(self) -> str:
        """Returns the full name of the reviewer."""
        return self.user.full_name if getattr(self, "user", None) else "Anonymous"
