from sqlalchemy import Column, Integer, Float, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    owner_id = Column(Integer, nullable=False, index=True)
    total_price = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
