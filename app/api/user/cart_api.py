from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.dependencies import get_db
from app.orders.services.cart_service import CartService
from app.orders.schemas.cart import CartItemCreate, CartResponse, CartItemResponse
from app.auth import get_current_user

router = APIRouter(tags=["Mobile - Cart"])

@router.post("/{owner_id}/items", response_model=CartItemResponse)
async def add_cart_item(owner_id: int, item: CartItemCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = CartService(db)
    return await service.add_item(user_id=current_user.id, owner_id=owner_id, item=item)

@router.get("/{owner_id}", response_model=CartResponse)
async def get_cart(owner_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = CartService(db)
    return await service.get_cart(user_id=current_user.id, owner_id=owner_id)

@router.patch("/{owner_id}/items/{item_id}", response_model=CartItemResponse)
async def update_cart_item(owner_id: int, item_id: int, quantity: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = CartService(db)
    return await service.update_item(user_id=current_user.id, owner_id=owner_id, cart_item_id=item_id, quantity=quantity)

@router.delete("/{owner_id}/items/{item_id}")
async def delete_cart_item(owner_id: int, item_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = CartService(db)
    await service.delete_item(user_id=current_user.id, owner_id=owner_id, cart_item_id=item_id)
    return {"detail": "Item removed from cart"}

@router.delete("/clear/{owner_id}")
async def clear_cart(owner_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = CartService(db)
    await service.clear_cart(user_id=current_user.id, owner_id=owner_id)
    return {"detail": "Cart cleared"}
