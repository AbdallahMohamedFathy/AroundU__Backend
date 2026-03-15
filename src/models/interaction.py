from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base
import enum

class InteractionType(str, enum.Enum):
    VISIT = "visit"
    CALL = "call"
    DIRECTION = "direction"
    ORDER = "order"
    SAVE = "save"

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # Optional user
    place_id = Column(Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False) # visit, call, direction, order, save
    user_lat = Column(Float, nullable=True)
    user_lon = Column(Float, nullable=True)
    cluster_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    place = relationship("Place", backref="interactions")
    user = relationship("User", backref="interactions")
