from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, nullable=False)  # reference to external Item table
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)

    cart = relationship("Cart", back_populates="items")
