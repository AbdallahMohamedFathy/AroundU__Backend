from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, func
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

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, nullable=False)  # reference to Item table (outside this module)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)

    cart = relationship("Cart", back_populates="items")
