from sqlalchemy import Column, Integer, Float, String, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.orders.enums.enums import OrderType, OrderStatus

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    owner_id = Column(Integer, nullable=False, index=True)
    order_type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    address = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    total_price = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    item_id = Column(Integer, nullable=False)  # reference to original Item
    item_name = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
