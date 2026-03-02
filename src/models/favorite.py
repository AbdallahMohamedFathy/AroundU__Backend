from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)

    # Ensure one user can't favorite the same place multiple times
    __table_args__ = (
        UniqueConstraint('user_id', 'place_id', name='unique_user_place_favorite'),
    )

    # Relationships
    user = relationship("User", back_populates="favorites")
    place = relationship("Place", back_populates="favorites")
