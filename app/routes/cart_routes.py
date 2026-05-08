from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.dependencies import get_db
from app.orders.services.cart_service import CartService
from app.orders.schemas.cart import CartItemCreate, CartResponse, CartItemResponse
from app.auth import get_current_user

router = APIRouter()

@router.post("/items", response_model=CartItemResponse)
async def add_cart_item(item: CartItemCreate, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = CartService(db)
    # owner_id must be provided in request body; for simplicity we assume it's in query param
    # In real implementation, owner_id would come from request payload or path
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Owner ID handling not implemented")

@router.get("/{owner_id}", response_model=CartResponse)
async def get_cart(owner_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = CartService(db)
    return await service.get_cart(user_id=current_user.id, owner_id=owner_id)

@router.patch("/items/{item_id}", response_model=CartItemResponse)
async def update_cart_item(item_id: int, quantity: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = CartService(db)
    # owner_id must be known; placeholder error
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Owner ID handling not implemented")

@router.delete("/items/{item_id}")
async def delete_cart_item(item_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = CartService(db)
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Owner ID handling not implemented")

@router.delete("/clear/{owner_id}")
async def clear_cart(owner_id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    service = CartService(db)
    await service.clear_cart(user_id=current_user.id, owner_id=owner_id)
    return {"detail": "Cart cleared"}
