from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from fastapi import HTTPException, status

from app.orders.models.order_models import Order, OrderItem
from app.orders.models.cart import Cart
from app.orders.models.cart_item import CartItem
from app.orders.enums.enums import OrderType, OrderStatus
from app.orders.repositories.order_repository import OrderRepository
from app.orders.repositories.cart_repository import CartRepository
from app.orders.schemas.order import OrderCreate, OrderItemCreate, OrderResponse, OrderItemResponse

class InvalidStatusTransition(Exception):
    pass

from src.models.place import Place

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)

    # ---------------------------------------------------------------------
    # Checkout
    # ---------------------------------------------------------------------
    async def checkout(self, user_id: int, order_data: OrderCreate) -> OrderResponse:
        # 1️⃣ Resolve owner_id from place_id (UX: User only deals with Place)
        place_result = await self.db.execute(select(Place).where(Place.id == order_data.place_id))
        place = place_result.scalars().first()
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")
        
        resolved_owner_id = place.owner_id

        # 2️⃣ Identify items to order (either from request body or from DB cart)
        items_to_order = []
        
        if order_data.items and len(order_data.items) > 0:
            # Use items provided directly in the request body
            items_to_order = order_data.items
        else:
            # Fallback to DB cart
            cart = await self.cart_repo.get_cart(user_id, resolved_owner_id)
            if not cart or not cart.items:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty and no items provided in request")
            items_to_order = cart.items

        # 3️⃣ Validate quantities
        for item in items_to_order:
            if item.quantity <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid quantity")

        # 4️⃣ Create Order and OrderItems inside a transaction
        async with self.db.begin():
            order = Order(
                user_id=user_id,
                owner_id=resolved_owner_id,
                place_id=order_data.place_id,
                order_type=order_data.order_type,
                status=OrderStatus.PENDING,
                full_name=order_data.full_name,
                phone_number=order_data.phone_number,
                address=order_data.address,
                notes=order_data.notes,
                total_price=0.0,
            )
            
            order_items: List[OrderItem] = []
            total_price = 0.0
            for item in items_to_order:
                # Use current item price and name
                price = getattr(item, 'unit_price', 0.0)
                name = getattr(item, 'item_name', f"Item {item.item_id}")
                
                item_snapshot = OrderItem(
                    order=order,
                    item_id=item.item_id,
                    item_name=name,
                    unit_price=price,
                    quantity=item.quantity,
                    total_price=price * item.quantity
                )
                order_items.append(item_snapshot)
                total_price += item_snapshot.total_price

            order.total_price = total_price
            await self.order_repo.create_order(order, order_items)

            # 5️⃣ Clear cart after successful order creation (only if we used the DB cart)
            if not (order_data.items and len(order_data.items) > 0):
                cart = await self.cart_repo.get_cart(user_id, owner_id)
                if cart:
                    await self.cart_repo.clear_cart(cart)

        # Return response
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            owner_id=order.owner_id,
            order_type=order.order_type,
            status=order.status,
            full_name=order.full_name,
            phone_number=order.phone_number,
            address=order.address,
            notes=order.notes,
            total_price=order.total_price,
            items=[
                OrderItemResponse(
                    id=item.id,
                    item_id=item.item_id,
                    item_name=item.item_name,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    total_price=item.total_price,
                )
                for item in order_items
            ],
            created_at=order.created_at.isoformat() if order.created_at else None,
        )

    # ---------------------------------------------------------------------
    # Status transition validation
    # ---------------------------------------------------------------------
    _valid_transitions = {
        OrderStatus.PENDING: {OrderStatus.ACCEPTED, OrderStatus.CANCELLED, OrderStatus.REJECTED},
        OrderStatus.ACCEPTED: {OrderStatus.PREPARING, OrderStatus.CANCELLED, OrderStatus.REJECTED},
        OrderStatus.PREPARING: {
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.READY_FOR_PICKUP,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        },
        OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.REJECTED},
        OrderStatus.DELIVERED: {OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REJECTED},
        OrderStatus.READY_FOR_PICKUP: {OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REJECTED},
        OrderStatus.COMPLETED: set(),
        OrderStatus.CANCELLED: set(),
        OrderStatus.REJECTED: set(),
    }

    _type_restrictions = {
        OrderType.TAKE_AWAY: {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED},
        OrderType.CASH_ON_DELIVERY: {OrderStatus.READY_FOR_PICKUP, OrderStatus.COMPLETED},
    }

    def _is_transition_allowed(self, current: OrderStatus, target: OrderStatus, order_type: OrderType) -> bool:
        # General flow check
        if target not in self._valid_transitions.get(current, set()):
            return False
        # Type‑specific restrictions
        restricted = self._type_restrictions.get(order_type, set())
        if target in restricted:
            return False
        return True

    async def change_status(self, order_id: int, new_status: OrderStatus, actor: str) -> OrderResponse:
        """Change order status.
        * `actor` = "user" or "owner" – used for permission checks (simplified).
        """
        order = await self.order_repo.get_order(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        # Permission checks (basic example)
        if actor == "user" and new_status not in {OrderStatus.CANCELLED, OrderStatus.REJECTED}:
            # Users can only cancel (or be rejected by system) – more granular rules can be added
            pass

        if not self._is_transition_allowed(order.status, new_status, order.order_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {order.status} to {new_status} for {order.order_type}",
            )
        await self.order_repo.update_status(order, new_status)
        # Refresh order to get latest data
        await self.db.refresh(order)
        # Build response
        items = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        items = items.scalars().all()
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            owner_id=order.owner_id,
            order_type=order.order_type,
            status=order.status,
            full_name=order.full_name,
            phone_number=order.phone_number,
            address=order.address,
            notes=order.notes,
            total_price=order.total_price,
            items=[
                OrderItemResponse(
                    id=i.id,
                    item_id=i.item_id,
                    item_name=i.item_name,
                    unit_price=i.unit_price,
                    quantity=i.quantity,
                    total_price=i.total_price,
                )
                for i in items
            ],
            created_at=order.created_at.isoformat() if order.created_at else None,
        )

    async def cancel_by_user(self, order_id: int, user_id: int) -> OrderResponse:
        order = await self.order_repo.get_order(order_id)
        if not order or order.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PENDING orders can be cancelled by user")
        await self.order_repo.cancel_order(order)
        await self.db.refresh(order)
        return await self.change_status(order_id, OrderStatus.CANCELLED, actor="user")
