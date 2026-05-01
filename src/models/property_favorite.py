from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base


class PropertyFavorite(Base):
    __tablename__ = "property_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)

    # Ensure one user can't favorite the same property multiple times
    __table_args__ = (
        UniqueConstraint('user_id', 'property_id', name='unique_user_property_favorite'),
    )

    # Relationships
    user = relationship("User", back_populates="property_favorites")
    prop = relationship("Property", back_populates="favorites")
