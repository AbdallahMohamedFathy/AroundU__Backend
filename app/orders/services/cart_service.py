from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models.cart import Cart
from app.orders.models.cart_item import CartItem
from app.orders.repositories.cart_repository import CartRepository
from app.orders.schemas.cart import CartItemCreate, CartResponse, CartItemResponse
from fastapi import HTTPException, status
from sqlalchemy import select
from src.models.item import Item
class CartService:
    def __init__(self, db: AsyncSession):
        self.repo = CartRepository(db)

    async def get_or_create_cart(self, user_id: int, place_id: int) -> Cart:
        cart = await self.repo.get_cart(user_id, place_id)
        if not cart:
            cart = await self.repo.create_cart(user_id, place_id)
        return cart

    async def add_item(self, user_id: int, place_id: int, item: CartItemCreate) -> CartItemResponse:
        # Cart is scoped per Place (branch) — items from another place not allowed
        cart = await self.get_or_create_cart(user_id, place_id)
        
        # Secure lookup: fetch the true item details from DB
        item_result = await self.repo.db.execute(select(Item).where(Item.id == item.item_id))
        db_item = item_result.scalars().first()
        if not db_item or db_item.is_deleted or not db_item.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item with id {item.item_id} is currently unavailable"
            )
            
        unit_price = float(db_item.price)
        
        cart_item = await self.repo.add_item(cart, item.item_id, item.quantity, unit_price)
        await self.repo.db.commit() # Ensure changes are saved
        
        return CartItemResponse(
            id=cart_item.id,
            item_id=cart_item.item_id,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            total_price=cart_item.unit_price * cart_item.quantity,
        )

    async def get_cart(self, user_id: int, place_id: int) -> CartResponse:
        cart = await self.repo.get_cart(user_id, place_id)
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
            place_id=cart.place_id,
            total_price=cart.total_price,
            items=items,
            created_at=cart.created_at.isoformat() if cart.created_at else None,
        )

    async def update_item(self, user_id: int, place_id: int, cart_item_id: int, quantity: int) -> CartItemResponse:
        cart = await self.repo.get_cart(user_id, place_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        try:
            cart_item = await self.repo.update_item(cart_item_id, quantity)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
            
        return CartItemResponse(
            id=cart_item.id,
            item_id=cart_item.item_id,
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            total_price=cart_item.unit_price * cart_item.quantity,
        )

    async def delete_item(self, user_id: int, place_id: int, cart_item_id: int) -> None:
        cart = await self.repo.get_cart(user_id, place_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        try:
            await self.repo.delete_item(cart_item_id)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def clear_cart(self, user_id: int, place_id: int) -> None:
        cart = await self.repo.get_cart(user_id, place_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
        await self.repo.clear_cart(cart)
