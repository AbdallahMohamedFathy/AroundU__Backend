from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models.cart import Cart
from app.orders.models.cart_item import CartItem
from app.orders.repositories.cart_repository import CartRepository
from app.orders.schemas.cart import CartItemCreate, CartResponse, CartItemResponse
from fastapi import HTTPException, status

class CartService:
    def __init__(self, db: AsyncSession):
        self.repo = CartRepository(db)

    async def get_or_create_cart(self, user_id: int, owner_id: int) -> Cart:
        cart = await self.repo.get_cart(user_id, owner_id)
        if not cart:
            cart = await self.repo.create_cart(user_id, owner_id)
        return cart

    async def add_item(self, user_id: int, owner_id: int, item: CartItemCreate) -> CartItemResponse:
        # Ensure a cart exists for this user/owner
        cart = await self.get_or_create_cart(user_id, owner_id)
        # Business rule: cart belongs to a single owner, enforced by owner_id check above
        cart_item = await self.repo.add_item(cart, item.item_id, item.quantity, item.unit_price)
        total_price = cart_item.unit_price * cart_item.quantity
        return CartItemResponse(
            id=cart_item.id,
            item_id=cart_item.item_id,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            total_price=total_price,
        )

    async def get_cart(self, user_id: int, owner_id: int) -> CartResponse:
        cart = await self.repo.get_cart(user_id, owner_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        items = [
            CartItemResponse(
                id=item.id,
                item_id=item.item_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.unit_price * item.quantity,
            )
            for item in cart.items
        ]
        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            owner_id=cart.owner_id,
            total_price=cart.total_price,
            items=items,
            created_at=cart.created_at.isoformat() if cart.created_at else None,
        )

    async def update_item(self, user_id: int, owner_id: int, cart_item_id: int, quantity: int) -> CartItemResponse:
        cart = await self.repo.get_cart(user_id, owner_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        cart_item = await self.repo.update_item(cart_item_id, quantity)
        return CartItemResponse(
            id=cart_item.id,
            item_id=cart_item.item_id,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            total_price=cart_item.unit_price * cart_item.quantity,
        )

    async def delete_item(self, user_id: int, owner_id: int, cart_item_id: int) -> None:
        cart = await self.repo.get_cart(user_id, owner_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        await self.repo.delete_item(cart_item_id)

    async def clear_cart(self, user_id: int, owner_id: int) -> None:
        cart = await self.repo.get_cart(user_id, owner_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        await self.repo.clear_cart(cart)
