from sqlalchemy import Column, Integer, Float, String, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.orders.enums.enums import OrderType, OrderStatus


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    place_id = Column(Integer, ForeignKey("places.id", ondelete="SET NULL"), nullable=True, index=True)
    order_type = Column(Enum(OrderType, native_enum=False, length=50), nullable=False)
    status = Column(Enum(OrderStatus, native_enum=False, length=50), nullable=False, default=OrderStatus.PENDING)
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
    item_id = Column(Integer, nullable=False)   # snapshot reference to original Item
    sub_item_id = Column(Integer, nullable=True)  # snapshot reference to SubItem (if selected)
    item_name = Column(String, nullable=False)  # snapshot — preserved even if item changes
    image_url = Column(String, nullable=True)   # snapshot image
    unit_price = Column(Float, nullable=False)  # snapshot — price at time of order
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
