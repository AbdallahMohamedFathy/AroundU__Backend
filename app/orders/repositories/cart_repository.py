from typing import Optional, List

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models.cart import Cart
from app.orders.models.cart_item import CartItem

class CartRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cart(self, user_id: int, owner_id: int) -> Optional[Cart]:
        result = await self.db.execute(
            select(Cart).where(Cart.user_id == user_id, Cart.owner_id == owner_id)
        )
        return result.scalars().first()

    async def create_cart(self, user_id: int, owner_id: int) -> Cart:
        cart = Cart(user_id=user_id, owner_id=owner_id, total_price=0.0)
        self.db.add(cart)
        await self.db.flush()
        return cart

    async def add_item(self, cart: Cart, item_id: int, quantity: int, unit_price: float) -> CartItem:
        # Check if item already exists in cart
        existing = await self.db.execute(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.item_id == item_id)
        )
        cart_item = existing.scalars().first()
        if cart_item:
            cart_item.quantity += quantity
            cart_item.unit_price = unit_price  # update price if needed
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                item_id=item_id,
                quantity=quantity,
                unit_price=unit_price,
            )
            self.db.add(cart_item)
        await self._recalculate_total(cart)
        return cart_item

    async def update_item(self, cart_item_id: int, quantity: int) -> CartItem:
        result = await self.db.execute(select(CartItem).where(CartItem.id == cart_item_id))
        cart_item = result.scalars().first()
        if not cart_item:
            raise ValueError("CartItem not found")
        cart_item.quantity = quantity
        await self._recalculate_total(cart_item.cart)
        return cart_item

    async def delete_item(self, cart_item_id: int) -> None:
        result = await self.db.execute(select(CartItem).where(CartItem.id == cart_item_id))
        cart_item = result.scalars().first()
        if not cart_item:
            raise ValueError("CartItem not found")
        await self.db.delete(cart_item)
        await self._recalculate_total(cart_item.cart)

    async def clear_cart(self, cart: Cart) -> None:
        await self.db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
        cart.total_price = 0.0
        await self.db.flush()

    async def _recalculate_total(self, cart: Cart) -> None:
        result = await self.db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
        items: List[CartItem] = result.scalars().all()
        cart.total_price = sum(item.unit_price * item.quantity for item in items)
        await self.db.flush()
