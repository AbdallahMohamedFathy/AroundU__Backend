import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi import HTTPException, status

from app.orders.models.order_models import Order, OrderItem
from app.orders.enums.enums import OrderType, OrderStatus
from app.orders.repositories.order_repository import OrderRepository
from app.orders.repositories.cart_repository import CartRepository
from app.orders.schemas.order import OrderCreate, OrderItemCreate, OrderResponse, OrderItemResponse

from src.models.place import Place
from src.models.item import Item
from src.models.sub_item import SubItem
from src.services.notification_service import send_order_status_notification

logger = logging.getLogger(__name__)

class InvalidStatusTransition(Exception):
    pass


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)

    # ------------------------------------------------------------------
    # Checkout
    # ------------------------------------------------------------------
    async def checkout(self, user_id: int, order_data: OrderCreate) -> OrderResponse:
        try:
            return await self._checkout_impl(user_id, order_data)
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            raise HTTPException(status_code=500, detail=str(error_details))

    async def _checkout_impl(self, user_id: int, order_data: OrderCreate) -> OrderResponse:
        # 1️⃣ Validate that the Place exists and is accepting orders
        place_result = await self.db.execute(select(Place).where(Place.id == order_data.place_id))
        place = place_result.scalars().first()
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")

        if not getattr(place, "is_accepting_orders", True):
            raise HTTPException(status_code=400, detail="This place is not accepting orders at the moment")

        if order_data.order_type == OrderType.CASH_ON_DELIVERY and not getattr(place, "accepts_delivery", True):
            raise HTTPException(status_code=400, detail="This place does not offer delivery")

        if order_data.order_type == OrderType.TAKE_AWAY and not getattr(place, "accepts_takeaway", True):
            raise HTTPException(status_code=400, detail="This place does not offer takeaway")

        # 2️⃣ Resolve items — from request body OR from DB cart for this place
        items_to_order: List[OrderItemCreate] = []

        if order_data.items and len(order_data.items) > 0:
            items_to_order = order_data.items
        else:
            # Fallback: use saved cart scoped to this place
            cart = await self.cart_repo.get_cart(user_id, order_data.place_id)
            if not cart or not cart.items:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cart is empty and no items provided in request"
                )
            items_to_order = cart.items

        # 3️⃣ Validate quantities
        for item in items_to_order:
            if item.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid quantity — must be greater than 0"
                )

        # 4️⃣ Create Order + OrderItems
        order = Order(
            user_id=user_id,
            place_id=order_data.place_id,
            order_type=order_data.order_type,
            status=OrderStatus.PENDING,
            full_name=order_data.full_name,
            phone_number=order_data.phone_number,
            address=order_data.address,
            notes=order_data.notes,
            total_price=0.0,
        )
        self.db.add(order)
        await self.db.flush()  # get order.id without committing

        order_items: List[OrderItem] = []
        total_price = 0.0

        for item in items_to_order:
            # Secure lookup: fetch the true item details from DB
            item_result = await self.db.execute(select(Item).where(Item.id == item.item_id))
            db_item = item_result.scalars().first()
            if not db_item or db_item.is_deleted or not db_item.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item with id {item.item_id} is currently unavailable"
                )

            price = float(db_item.price)
            name = db_item.name

            # If sub_item_id is provided, use the sub-item's price instead of the parent item price
            if item.sub_item_id:
                sub_item_result = await self.db.execute(
                    select(SubItem).where(
                        SubItem.id == item.sub_item_id,
                        SubItem.item_id == item.item_id,
                        SubItem.is_deleted == False,
                        SubItem.is_available == True,
                    )
                )
                db_sub_item = sub_item_result.scalars().first()
                if not db_sub_item:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Sub-item with id {item.sub_item_id} is unavailable or does not belong to item {item.item_id}"
                    )
                price = float(db_sub_item.price)
                name = f"{db_item.name} - {db_sub_item.name}"

            item_snapshot = OrderItem(
                order_id=order.id,
                item_id=item.item_id,
                sub_item_id=item.sub_item_id,
                item_name=name,
                image_url=db_item.image_url,
                unit_price=price,
                quantity=item.quantity,
                total_price=price * item.quantity,
            )
            self.db.add(item_snapshot)
            order_items.append(item_snapshot)
            total_price += item_snapshot.total_price

        order.total_price = total_price
        await self.db.flush()

        # 5️⃣ Clear cart after checkout (only if we used the saved cart)
        if not (order_data.items and len(order_data.items) > 0):
            cart = await self.cart_repo.get_cart(user_id, order_data.place_id)
            if cart:
                await self.cart_repo.clear_cart(cart)

        await self.db.commit()
        await self.db.refresh(order)

        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            place_id=order.place_id,
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
                    image_url=item.image_url,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    total_price=item.total_price,
                )
                for item in order_items
            ],
            created_at=order.created_at,
        )

    # ------------------------------------------------------------------
    # Status Transition Rules
    # ------------------------------------------------------------------
    _valid_transitions = {
        OrderStatus.PENDING:          {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
        OrderStatus.CONFIRMED:        {OrderStatus.PREPARING, OrderStatus.CANCELLED},
        OrderStatus.PREPARING:        {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.READY_FOR_PICKUP, OrderStatus.CANCELLED},
        OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.COMPLETED, OrderStatus.CANCELLED},
        OrderStatus.READY_FOR_PICKUP: {OrderStatus.COMPLETED, OrderStatus.CANCELLED},
        OrderStatus.COMPLETED:        set(),
        OrderStatus.CANCELLED:        set(),
    }

    _type_restrictions = {
        OrderType.TAKE_AWAY:        {OrderStatus.OUT_FOR_DELIVERY},
        OrderType.CASH_ON_DELIVERY: {OrderStatus.READY_FOR_PICKUP},
    }

    async def _get_place_name(self, place_id: Optional[int]) -> str:
        if not place_id:
            return ""
        try:
            result = await self.db.execute(select(Place).where(Place.id == place_id))
            place = result.scalars().first()
            return place.name if place else ""
        except Exception:
            return ""

    def _is_transition_allowed(self, current: OrderStatus, target: OrderStatus, order_type: OrderType) -> bool:
        if target not in self._valid_transitions.get(current, set()):
            return False
        restricted = self._type_restrictions.get(order_type, set())
        if target in restricted:
            return False
        return True

    async def change_status(self, order_id: int, new_status: OrderStatus) -> OrderResponse:
        order = await self.order_repo.get_order(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        if not self._is_transition_allowed(order.status, new_status, order.order_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition: {order.status} → {new_status} for type {order.order_type}",
            )

        await self.order_repo.update_status(order, new_status)
        await self.db.commit()
        await self.db.refresh(order)

        items_result = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        items = items_result.scalars().all()

        response = OrderResponse(
            id=order.id,
            user_id=order.user_id,
            place_id=order.place_id,
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
                    image_url=i.image_url,
                    unit_price=i.unit_price,
                    quantity=i.quantity,
                    total_price=i.total_price,
                )
                for i in items
            ],
            created_at=order.created_at,
        )

        place_name = await self._get_place_name(order.place_id)
        try:
            await send_order_status_notification(
                self.db, order.user_id, order.id, new_status.value, place_name
            )
        except Exception as e:
            logger.warning(f"FCM notification failed for order {order_id}: {e}")

        return response

    async def cancel_by_user(self, order_id: int, user_id: int) -> OrderResponse:
        order = await self.order_repo.get_order(order_id)
        if not order or order.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PENDING orders can be cancelled by the user"
            )
        order.status = OrderStatus.CANCELLED
        await self.db.commit()
        await self.db.refresh(order)
        items_result = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        items = items_result.scalars().all()

        response = OrderResponse(
            id=order.id,
            user_id=order.user_id,
            place_id=order.place_id,
            order_type=order.order_type,
            status=order.status,
            full_name=order.full_name,
            phone_number=order.phone_number,
            address=order.address,
            notes=order.notes,
            total_price=order.total_price,
            items=[
                OrderItemResponse(id=i.id, item_id=i.item_id, item_name=i.item_name, image_url=i.image_url,
                                  unit_price=i.unit_price, quantity=i.quantity, total_price=i.total_price)
                for i in items
            ],
            created_at=order.created_at,
        )

        place_name = await self._get_place_name(order.place_id)
        try:
            await send_order_status_notification(
                self.db, order.user_id, order.id, OrderStatus.CANCELLED.value, place_name
            )
        except Exception as e:
            logger.warning(f"FCM notification failed for cancelled order {order_id}: {e}")

        return response
