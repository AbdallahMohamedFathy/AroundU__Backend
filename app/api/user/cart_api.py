from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_db
from app.orders.services.cart_service import CartService
from app.orders.schemas.cart import CartItemCreate, CartResponse, CartItemResponse
from app.auth import get_current_user

router = APIRouter(tags=["Mobile - Cart"])


@router.post(
    "/{place_id}/items",
    response_model=CartItemResponse,
    summary="Add Item to Cart",
    description="Add an item to the cart for a specific **place (branch)**. Cart is scoped per place — you cannot mix items from different places."
)
async def add_cart_item(
    place_id: int,
    item: CartItemCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CartService(db)
    return await service.add_item(user_id=current_user.id, place_id=place_id, item=item)


@router.get(
    "/{place_id}",
    response_model=CartResponse,
    summary="Get Cart",
    description="Retrieve the current user's cart for a specific **place (branch)**."
)
async def get_cart(
    place_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CartService(db)
    return await service.get_cart(user_id=current_user.id, place_id=place_id)


@router.patch(
    "/{place_id}/items/{item_id}",
    response_model=CartItemResponse,
    summary="Update Cart Item Quantity",
    description="Update quantity of an item in the cart for a specific **place (branch)**."
)
async def update_cart_item(
    place_id: int,
    item_id: int,
    quantity: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CartService(db)
    return await service.update_item(
        user_id=current_user.id, place_id=place_id, cart_item_id=item_id, quantity=quantity
    )


@router.delete(
    "/{place_id}/items/{item_id}",
    summary="Remove Item from Cart",
    description="Remove a specific item from the cart for a **place (branch)**."
)
async def delete_cart_item(
    place_id: int,
    item_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CartService(db)
    await service.delete_item(user_id=current_user.id, place_id=place_id, cart_item_id=item_id)
    return {"detail": "Item removed from cart"}


@router.delete(
    "/clear/{place_id}",
    summary="Clear Cart",
    description="Clear all items from the cart for a specific **place (branch)**."
)
async def clear_cart(
    place_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CartService(db)
    await service.clear_cart(user_id=current_user.id, place_id=place_id)
    return {"detail": "Cart cleared"}
