from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models.order_models import Order, OrderItem
from app.orders.enums.enums import OrderStatus


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_order(self, order_id: int) -> Optional[Order]:
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
        return result.scalars().first()

    async def get_user_orders(self, user_id: int) -> List[Order]:
        result = await self.db.execute(
            select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_place_orders(self, place_id: int) -> List[Order]:
        """Return all orders for a specific place (branch) — used by owner dashboard."""
        result = await self.db.execute(
            select(Order).where(Order.place_id == place_id).order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_owner_orders(self, owner_id: int) -> List[Order]:
        """Return all orders across ALL places belonging to this owner — requires JOIN with Place."""
        from src.models.place import Place
        result = await self.db.execute(
            select(Order)
            .join(Place, Order.place_id == Place.id)
            .where(Place.owner_id == owner_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def get_all_orders(self) -> List[Order]:
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    async def create_order(self, order: Order, items: List[OrderItem]) -> Order:
        self.db.add(order)
        for item in items:
            self.db.add(item)
        await self.db.flush()
        await self.db.refresh(order)
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
