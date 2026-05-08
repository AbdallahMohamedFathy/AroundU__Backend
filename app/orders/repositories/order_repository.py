from typing import Optional, List

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models.order_models import Order, OrderItem
# Removed duplicate import; OrderItem is imported from order_models
from app.orders.enums.enums import OrderStatus

class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_order(self, order_id: int) -> Optional[Order]:
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        return result.scalars().first()

    async def get_user_orders(self, user_id: int) -> List[Order]:
        result = await self.db.execute(select(Order).where(Order.user_id == user_id))
        return result.scalars().all()

    async def get_owner_orders(self, owner_id: int) -> List[Order]:
        result = await self.db.execute(select(Order).where(Order.owner_id == owner_id))
        return result.scalars().all()

    async def create_order(self, order: Order, items: List[OrderItem]) -> Order:
        self.db.add(order)
        for item in items:
            self.db.add(item)
        await self.db.flush()
        return order

    async def update_status(self, order: Order, new_status: OrderStatus) -> Order:
        order.status = new_status
        await self.db.flush()
        return order

    async def cancel_order(self, order: Order) -> Order:
        order.status = OrderStatus.CANCELLED
        await self.db.flush()
        return order

    async def count_orders(self) -> int:
        result = await self.db.execute(select(func.count(Order.id)))
        return result.scalar_one() or 0
        return result.scalar() or 0
